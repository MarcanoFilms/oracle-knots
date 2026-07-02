/* Oracle Knots — Mempool Explorer
 * 3D live mempool (Three.js), block/tx/address exploration, txindex UX.
 * Exposes window.OracleExplorer = { onTabShow, onTabHide, refresh }.
 */
(function () {
    'use strict';

    const POLL_MS = 10000;
    const PROJECTED_BLOCKS = 4;
    const MAX_VISIBLE_TX_PER_BLOCK = 400;
    const MAX_INSTANCES = MAX_VISIBLE_TX_PER_BLOCK * PROJECTED_BLOCKS;
    const MINE_ANIM_MS = 800;
    const BLOCK_BOX_SIZE = 10;
    const BLOCK_SPACING = 14;
    const TEMPLATE_INDEX = 0;   // right-most in scene: index 0 (next block being built)

    let inited = false;
    let visible = false;
    let nodeRunning = false;
    let pollTimer = null;
    let capabilities = null;

    // --- DOM ---
    let $ = (id) => document.getElementById(id);
    let searchInput, searchBtn, searchError, txBanner, txBannerDetail, txBannerBtn;
    let hudTxCount, hudVsize, hudMinFee, canvasWrap, canvas, tooltip, webglFallback;
    let projectedStrip, blocksStrip, tipBadge, drawer, drawerTitle, drawerBody;

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g,
            c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }
    function fmtNum(n) { return n == null ? '—' : Number(n).toLocaleString(); }
    function fmtBtc(v) { return v == null ? '—' : `${Number(v).toFixed(8)} BTC`; }
    function shortId(id, n) { n = n || 10; return id ? `${id.slice(0, n)}…${id.slice(-n)}` : '—'; }
    function fmtAge(ts) {
        if (!ts) return '—';
        const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
        if (s < 60) return `${s}s ago`;
        if (s < 3600) return `${Math.floor(s / 60)}m ago`;
        if (s < 86400) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m ago`;
        return `${Math.floor(s / 86400)}d ago`;
    }

    // =====================================================================
    // 3D scene
    // =====================================================================
    let renderer = null, scene = null, camera = null, raycaster = null;
    let mesh = null;
    let sceneReady = false;
    let animating = false;
    let clockT = 0;

    // Chain block cages: { group, edges, fill, hidden, label } per block index (0 = template)
    let cages = [];
    let chainLinks = null;

    // orbit state — start looking at the chain from a slight side-angle above
    const orbit = { theta: -0.4, phi: 1.1, radius: 42, target: null, dragging: false,
                    lastX: 0, lastY: 0, idle: true };

    // per-instance state
    // slots[i] = { txid, feerate, vsize, target:{x,y,z}, pos:{x,y,z}, scale, targetScale, block }
    let slots = [];
    let txSlot = new Map();     // txid -> slot index
    let freeSlots = [];
    let lastSnapshot = null;
    let hoverInstance = -1;
    let lastTipHeight = null;
    let miningAnimUntil = 0;
    let mineFlashLabel = null;

    const _dummy = { obj: null };

    function txJitter(txid, salt) {
        // deterministic pseudo-random in [-0.5, 0.5) from txid hex
        let h = 0;
        for (let i = 0; i < 16; i++) h = ((h << 5) - h + txid.charCodeAt((i + salt * 7) % txid.length)) | 0;
        return ((h >>> 0) % 1000) / 1000 - 0.5;
    }

    function feeColor(rate) {
        // deep-teal -> cyan -> purple -> hot pink, log-ish scale 1..300 s/vB
        // Deep-teal at the bottom keeps low-fee cubes readable against black instead of pure white glow.
        const t = Math.min(1, Math.max(0, Math.log10(Math.max(rate, 1)) / Math.log10(300)));
        const c = new THREE.Color();
        if (t < 0.33) c.lerpColors(new THREE.Color(0x0a4a5c), new THREE.Color(0x00f0ff), t / 0.33);
        else if (t < 0.66) c.lerpColors(new THREE.Color(0x00f0ff), new THREE.Color(0xbd5eff), (t - 0.33) / 0.33);
        else c.lerpColors(new THREE.Color(0xbd5eff), new THREE.Color(0xff4fd8), (t - 0.66) / 0.34);
        return c;
    }

    function initScene() {
        if (sceneReady) return true;
        if (typeof THREE === 'undefined') return failWebgl('Three.js failed to load.');
        try {
            renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
        } catch (e) {
            return failWebgl('WebGL is not available on this system.');
        }
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

        scene = new THREE.Scene();
        scene.fog = new THREE.Fog(0x05070e, 80, 180);
        camera = new THREE.PerspectiveCamera(48, 1, 0.1, 300);
        orbit.target = new THREE.Vector3(0, 0, 0);
        raycaster = new THREE.Raycaster();
        _dummy.obj = new THREE.Object3D();

        // Single InstancedMesh for tx cubes (no additive glow twin — was saturating to white)
        const geo = new THREE.BoxGeometry(1, 1, 1);
        const mat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.82 });
        mesh = new THREE.InstancedMesh(geo, mat, MAX_INSTANCES);
        mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
        mesh.count = 0;
        scene.add(mesh);

        // Grid floor for depth reference
        const grid = new THREE.GridHelper(160, 40, 0x123a4a, 0x0b1526);
        grid.position.y = -6;
        scene.add(grid);

        // Chain of wireframe cages: index 0 = template (rightmost), 1..3 = +1..+3 blocks
        buildChainCages();

        bindOrbitControls();
        window.addEventListener('resize', resizeRenderer);
        resizeRenderer();
        sceneReady = true;
        return true;
    }

    function buildChainCages() {
        const boxGeo = new THREE.BoxGeometry(BLOCK_BOX_SIZE, BLOCK_BOX_SIZE, BLOCK_BOX_SIZE);
        const edgesGeo = new THREE.EdgesGeometry(boxGeo);

        for (let bi = 0; bi < PROJECTED_BLOCKS; bi++) {
            const isTemplate = (bi === TEMPLATE_INDEX);
            const group = new THREE.Group();
            const o = blockOrigin(bi);
            group.position.set(o.x, 0, 0);

            // Wireframe cage
            const edgeMat = new THREE.LineBasicMaterial({
                color: 0x00f0ff,
                transparent: true,
                opacity: isTemplate ? 0.9 : Math.max(0.18, 0.5 - bi * 0.1),
            });
            const edges = new THREE.LineSegments(edgesGeo, edgeMat);
            group.add(edges);

            // Fill-level slab (proportional to fill_pct) — all cages, dimmer toward +N
            const fillGeo = new THREE.BoxGeometry(BLOCK_BOX_SIZE * 0.94, 1, BLOCK_BOX_SIZE * 0.94);
            const fillMat = new THREE.MeshBasicMaterial({
                color: isTemplate ? 0x00f0ff : 0x7a5cff,
                transparent: true,
                opacity: isTemplate ? 0.06 : Math.max(0.02, 0.05 - bi * 0.01),
                depthWrite: false,
            });
            const fill = new THREE.Mesh(fillGeo, fillMat);
            fill.position.y = -BLOCK_BOX_SIZE / 2 + 0.5;
            group.add(fill);

            scene.add(group);
            const label = document.createElement('div');
            label.className = 'explorer-block-label' + (isTemplate ? ' explorer-block-label--template' : '');
            label.style.display = 'none';
            canvasWrap.appendChild(label);

            cages.push({ group, edges, fill, hidden: 0, label, isTemplate });
        }

        // Chain links between consecutive cages
        const linkMat = new THREE.LineBasicMaterial({
            color: 0x00f0ff, transparent: true, opacity: 0.25 });
        const linkPoints = [];
        for (let bi = 0; bi < cages.length - 1; bi++) {
            const a = blockOrigin(bi), b = blockOrigin(bi + 1);
            linkPoints.push(new THREE.Vector3(a.x - BLOCK_BOX_SIZE / 2, 0, 0));
            linkPoints.push(new THREE.Vector3(b.x + BLOCK_BOX_SIZE / 2, 0, 0));
        }
        if (linkPoints.length) {
            const linkGeo = new THREE.BufferGeometry().setFromPoints(linkPoints);
            chainLinks = new THREE.LineSegments(linkGeo, linkMat);
            scene.add(chainLinks);
        }
    }

    function failWebgl(msg) {
        if (canvas) canvas.classList.add('hidden');
        if (webglFallback) {
            webglFallback.classList.remove('hidden');
            webglFallback.innerHTML = `<p class="text-secondary">${esc(msg)} Showing the fee histogram instead.</p><div id="explorer-hist-2d"></div>`;
        }
        return false;
    }

    function resizeRenderer() {
        if (!renderer || !canvasWrap) return;
        const w = canvasWrap.clientWidth, h = canvasWrap.clientHeight || 420;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    }

    function bindOrbitControls() {
        canvas.addEventListener('pointerdown', (e) => {
            orbit.dragging = true; orbit.idle = false;
            orbit.lastX = e.clientX; orbit.lastY = e.clientY;
            canvas.setPointerCapture(e.pointerId);
        });
        canvas.addEventListener('pointerup', (e) => {
            orbit.dragging = false;
            setTimeout(() => { orbit.idle = true; }, 4000);
            canvas.releasePointerCapture(e.pointerId);
        });
        canvas.addEventListener('pointermove', (e) => {
            if (orbit.dragging) {
                orbit.theta -= (e.clientX - orbit.lastX) * 0.006;
                orbit.phi = Math.min(1.5, Math.max(0.25, orbit.phi - (e.clientY - orbit.lastY) * 0.005));
                orbit.lastX = e.clientX; orbit.lastY = e.clientY;
            } else {
                throttledHover(e);
            }
        });
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            orbit.radius = Math.min(120, Math.max(14, orbit.radius + e.deltaY * 0.04));
        }, { passive: false });
        canvas.addEventListener('click', onCanvasClick);
    }

    function applyCamera() {
        if (orbit.idle && !orbit.dragging) orbit.theta += 0.0012;
        const t = orbit.target;
        camera.position.set(
            t.x + orbit.radius * Math.sin(orbit.phi) * Math.cos(orbit.theta),
            t.y + orbit.radius * Math.cos(orbit.phi),
            t.z + orbit.radius * Math.sin(orbit.phi) * Math.sin(orbit.theta)
        );
        camera.lookAt(t);
    }

    function pointerNDC(e) {
        const r = canvas.getBoundingClientRect();
        return { x: ((e.clientX - r.left) / r.width) * 2 - 1,
                 y: -((e.clientY - r.top) / r.height) * 2 + 1 };
    }

    let lastHoverTs = 0;
    function throttledHover(e) {
        const now = performance.now();
        if (now - lastHoverTs < 100 || !sceneReady) return;
        lastHoverTs = now;
        const ndc = pointerNDC(e);
        raycaster.setFromCamera(ndc, camera);
        const hits = raycaster.intersectObject(mesh);
        const id = hits.length ? hits[0].instanceId : -1;
        if (id !== hoverInstance) {
            hoverInstance = id;
            canvas.style.cursor = id >= 0 ? 'pointer' : 'grab';
        }
        if (id >= 0 && slots[id] && slots[id].txid) {
            const s = slots[id];
            tooltip.innerHTML = `<span class="font-mono">${esc(s.txid.slice(0, 16))}…</span><br>` +
                `${fmtNum(s.vsize)} vB · <strong>${s.feerate} sat/vB</strong>`;
            tooltip.style.left = `${e.clientX - canvasWrap.getBoundingClientRect().left + 14}px`;
            tooltip.style.top = `${e.clientY - canvasWrap.getBoundingClientRect().top - 8}px`;
            tooltip.classList.remove('hidden');
        } else {
            tooltip.classList.add('hidden');
        }
    }

    function onCanvasClick(e) {
        if (!sceneReady || orbit.dragging) return;
        const ndc = pointerNDC(e);
        raycaster.setFromCamera(ndc, camera);
        const hits = raycaster.intersectObject(mesh);
        if (hits.length && slots[hits[0].instanceId] && slots[hits[0].instanceId].txid) {
            openTxDetail(slots[hits[0].instanceId].txid);
        }
    }

    // Layout: template (idx 0) sits at x=0 on the right; +1, +2, +3 stretch to the left.
    function blockOrigin(blockIdx) {
        return { x: -blockIdx * BLOCK_SPACING, y: 0, z: 0 };
    }

    // Position tx inside a fixed-size 3D grid contained within the cage.
    function slotTargetFor(txid, blockIdx, posInBlock) {
        const cols = 8, rows = 8;
        const perLayer = cols * rows;
        const layers = Math.ceil(MAX_VISIBLE_TX_PER_BLOCK / perLayer);
        const cell = posInBlock % perLayer;
        const layer = Math.min(layers - 1, Math.floor(posInBlock / perLayer));
        const spacing = (BLOCK_BOX_SIZE - 1.2) / Math.max(cols - 1, layers - 1, 1);
        const gx = (cell % cols) - (cols - 1) / 2;
        const gz = Math.floor(cell / cols) - (rows - 1) / 2;
        const o = blockOrigin(blockIdx);
        return {
            x: o.x + gx * spacing + txJitter(txid, 1) * spacing * 0.25,
            y: -BLOCK_BOX_SIZE / 2 + 0.6 + layer * spacing + txJitter(txid, 2) * spacing * 0.2,
            z: o.z + gz * spacing + txJitter(txid, 3) * spacing * 0.25,
        };
    }

    function applySnapshot(data) {
        lastSnapshot = data;
        if (!sceneReady) return;

        // Backend order: projected_blocks[0] = next block, [1] = +1, [2] = +2 — matches our
        // scene index directly (0 = template on the right, growing to the left).
        const incoming = new Map();
        const hidden = new Array(cages.length).fill(0);
        (data.projected_blocks || []).forEach((b, bi) => {
            if (bi >= cages.length) return;
            const total = b.tx_count != null ? b.tx_count : b.txs.length;
            b.txs.forEach((t, ti) => {
                if (ti >= MAX_VISIBLE_TX_PER_BLOCK) return;
                incoming.set(t[0], { vsize: t[1], feerate: t[2], block: bi, posInBlock: ti });
            });
            hidden[bi] = Math.max(0, total - Math.min(b.txs.length, MAX_VISIBLE_TX_PER_BLOCK));
        });
        for (let bi = 0; bi < cages.length; bi++) cages[bi].hidden = hidden[bi];

        // departures
        for (const [txid, i] of txSlot) {
            if (!incoming.has(txid)) {
                slots[i].targetScale = 0;
                slots[i].dying = true;
            }
        }
        // arrivals + moves
        for (const [txid, info] of incoming) {
            let i = txSlot.get(txid);
            const target = slotTargetFor(txid, info.block, info.posInBlock);
            // Confined to a fixed cage, so scale range is much smaller than before.
            const scale = Math.min(0.5, Math.max(0.14, Math.cbrt(info.vsize) / 14));
            if (i === undefined) {
                i = freeSlots.length ? freeSlots.pop() : slots.length;
                if (i >= MAX_INSTANCES) continue;
                slots[i] = {
                    txid, vsize: info.vsize, feerate: info.feerate, block: info.block,
                    pos: { x: target.x, y: target.y + 2.5, z: target.z },  // spawn just above target
                    target, scale: 0.01, targetScale: scale, dying: false,
                };
                txSlot.set(txid, i);
                mesh.setColorAt(i, feeColor(info.feerate));
            } else {
                const s = slots[i];
                s.vsize = info.vsize; s.feerate = info.feerate; s.block = info.block;
                s.target = target; s.targetScale = scale; s.dying = false;
                mesh.setColorAt(i, feeColor(info.feerate));
            }
        }
        mesh.count = slots.length;
        if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    }

    function tick() {
        if (!animating) return;
        clockT += 1 / 60;
        const d = _dummy.obj;
        for (let i = 0; i < slots.length; i++) {
            const s = slots[i];
            if (!s) continue;
            s.pos.x += (s.target.x - s.pos.x) * 0.08;
            s.pos.y += (s.target.y - s.pos.y) * 0.08;
            s.pos.z += (s.target.z - s.pos.z) * 0.08;
            s.scale += (s.targetScale - s.scale) * 0.1;
            if (s.dying && s.scale < 0.02) {
                txSlot.delete(s.txid);
                s.txid = null; s.dying = false; s.scale = 0; s.targetScale = 0;
                freeSlots.push(i);
            }
            const sc = Math.max(s.scale, 0.0001);
            d.position.set(s.pos.x, s.pos.y, s.pos.z);
            d.scale.set(sc, sc, sc);
            d.updateMatrix();
            mesh.setMatrixAt(i, d.matrix);
        }
        mesh.instanceMatrix.needsUpdate = true;

        // Template cage pulse + fill level + label projection for each cage
        updateCagesFrame();
        applyCamera();
        renderer.render(scene, camera);
        updateCageLabels();
    }

    function updateCagesFrame() {
        if (!lastSnapshot) return;
        const projected = lastSnapshot.projected_blocks || [];
        const mining = performance.now() < miningAnimUntil;
        for (let bi = 0; bi < cages.length; bi++) {
            const cage = cages[bi];
            const b = projected[bi];
            if (cage.fill && b) {
                const h = Math.max(0.15, (b.fill_pct / 100) * BLOCK_BOX_SIZE);
                cage.fill.scale.y = h;
                cage.fill.position.y = -BLOCK_BOX_SIZE / 2 + h / 2;
            }
            if (cage.isTemplate) {
                const pulse = mining
                    ? 1 + Math.sin(clockT * 8) * 0.06
                    : 1 + Math.sin(clockT * 2.4) * 0.02;
                cage.group.scale.setScalar(pulse);
                if (cage.fill && b) {
                    const base = mining ? 0.14 : 0.06;
                    cage.fill.material.opacity = base + Math.sin(clockT * (mining ? 8 : 2.4)) * 0.04;
                }
                if (cage.edges && cage.edges.material) {
                    cage.edges.material.opacity = mining ? 1 : 0.9;
                }
            }
        }
    }

    function triggerMineAnimation() {
        miningAnimUntil = performance.now() + MINE_ANIM_MS;
        for (const [, i] of txSlot) {
            const s = slots[i];
            if (s && s.block === TEMPLATE_INDEX && !s.dying) {
                s.dying = true;
                s.targetScale = 0;
                s.target.y += 4;
            }
        }
        if (!mineFlashLabel && canvasWrap) {
            mineFlashLabel = document.createElement('div');
            mineFlashLabel.className = 'explorer-block-label explorer-block-label--template';
            mineFlashLabel.style.pointerEvents = 'none';
            canvasWrap.appendChild(mineFlashLabel);
        }
        if (mineFlashLabel) {
            mineFlashLabel.innerHTML = '<div class="ebl-title">BLOCK MINED</div>';
            mineFlashLabel.style.display = '';
        }
    }

    const _labelVec = { v: null };
    function updateCageLabels() {
        if (!_labelVec.v) _labelVec.v = new THREE.Vector3();
        const projected = (lastSnapshot && lastSnapshot.projected_blocks) || [];
        const rect = canvas.getBoundingClientRect();
        for (let bi = 0; bi < cages.length; bi++) {
            const cage = cages[bi];
            const b = projected[bi];
            if (!b) { cage.label.style.display = 'none'; continue; }
            // Position: top of the cage
            _labelVec.v.set(blockOrigin(bi).x, BLOCK_BOX_SIZE / 2 + 1.4, 0);
            _labelVec.v.project(camera);
            const x = (_labelVec.v.x * 0.5 + 0.5) * rect.width;
            const y = (-_labelVec.v.y * 0.5 + 0.5) * rect.height;
            if (_labelVec.v.z > 1 || _labelVec.v.z < -1) {
                cage.label.style.display = 'none';
                continue;
            }
            cage.label.style.display = '';
            cage.label.style.left = `${x}px`;
            cage.label.style.top = `${y}px`;
            const title = cage.isTemplate
                ? 'NEXT BLOCK'
                : `+${bi} block`;
            const extra = cage.hidden > 0 ? ` · +${fmtNum(cage.hidden)} hidden` : '';
            cage.label.innerHTML = `<div class="ebl-title">${title}</div>` +
                `<div class="ebl-fee">~${b.median_feerate} sat/vB</div>` +
                `<div class="ebl-meta">${fmtNum(b.tx_count)} txs · ${b.fill_pct}%${extra}</div>`;
        }
        if (mineFlashLabel) {
            if (performance.now() < miningAnimUntil) {
                _labelVec.v.set(blockOrigin(TEMPLATE_INDEX).x, BLOCK_BOX_SIZE / 2 + 3.2, 0);
                _labelVec.v.project(camera);
                const x = (_labelVec.v.x * 0.5 + 0.5) * rect.width;
                const y = (-_labelVec.v.y * 0.5 + 0.5) * rect.height;
                mineFlashLabel.style.left = `${x}px`;
                mineFlashLabel.style.top = `${y}px`;
                mineFlashLabel.style.display = '';
            } else {
                mineFlashLabel.style.display = 'none';
            }
        }
    }

    function startLoop() {
        if (!sceneReady || animating) return;
        animating = true;
        renderer.setAnimationLoop(tick);
    }
    function stopLoop() {
        animating = false;
        if (renderer) renderer.setAnimationLoop(null);
    }

    // =====================================================================
    // Data fetching / HUD / strips
    // =====================================================================
    async function fetchMempool() {
        try {
            const res = await fetch('/api/explorer/mempool');
            const data = await res.json();
            if (!data.online) { renderOffline(); return; }
            renderHud(data);
            renderProjectedStrip(data);
            if (sceneReady) applySnapshot(data);
            else if (webglFallback && !webglFallback.classList.contains('hidden')) renderHistogram2d(data);
        } catch (e) { /* transient */ }
    }

    function renderOffline() {
        hudTxCount.textContent = 'node offline';
        hudVsize.textContent = '— vB';
        hudMinFee.textContent = 'min — s/vB';
        projectedStrip.innerHTML = '';
    }

    function renderHud(data) {
        const mi = data.mempoolinfo || {};
        hudTxCount.textContent = `${fmtNum(mi.size)} txs`;
        const kvb = Math.round((mi.bytes || 0) / 1000);
        let vs = `${fmtNum(kvb)} kvB`;
        if (data.tail_tx_count > 0) {
            vs += ` · queue +${fmtNum(data.tail_tx_count)} (~${data.tail_full_blocks} blocks)`;
        }
        hudVsize.textContent = vs;
        const minFee = mi.mempoolminfee != null ? Math.round(mi.mempoolminfee * 1e8 / 1000 * 10) / 10 : null;
        hudMinFee.textContent = `min ${minFee != null ? minFee : '—'} s/vB`;
    }

    function renderProjectedStrip(data) {
        const blocks = data.projected_blocks || [];
        // Cards mirror the scene: index 0 is the live template (rightmost); rest are +1, +2, +3.
        let html = blocks.map((b, i) => `
            <div class="projected-block-card ${i === 0 ? 'pbc-template' : ''}" data-block="${i}">
                <div class="pbc-title">${i === 0 ? 'Next block · live' : `+${i}`}</div>
                <div class="pbc-fee font-mono">~${b.median_feerate} sat/vB</div>
                <div class="pbc-meta">${fmtNum(b.tx_count)} txs · ${(b.total_fees_sat / 1e8).toFixed(4)} BTC fees</div>
                <div class="pbc-fill-track"><div class="pbc-fill" style="width:${b.fill_pct}%"></div></div>
            </div>`).join('');
        if (data.tail_tx_count > 0) {
            html += `
            <div class="projected-block-card pbc-tail">
                <div class="pbc-title">Queue</div>
                <div class="pbc-fee font-mono">~${data.tail_full_blocks || 0} blocks</div>
                <div class="pbc-meta">${fmtNum(data.tail_tx_count)} txs waiting</div>
                <div class="pbc-fill-track"><div class="pbc-fill" style="width:100%"></div></div>
            </div>`;
        }
        projectedStrip.innerHTML = html;
        projectedStrip.querySelectorAll('[data-block]').forEach(el => {
            el.addEventListener('click', () => {
                const o = blockOrigin(parseInt(el.dataset.block, 10));
                if (orbit.target) { orbit.target.set(o.x, 0, o.z); orbit.radius = 26; orbit.idle = false; }
            });
        });
    }

    function renderHistogram2d(data) {
        const host = $('explorer-hist-2d');
        if (!host) return;
        const rows = [];
        (data.projected_blocks || []).forEach((b, i) =>
            rows.push({ label: `block +${i + 1} (~${b.median_feerate} s/vB)`, count: b.tx_count }));
        (data.histogram || []).forEach(h => rows.push({ label: `${h.bucket} s/vB`, count: h.count }));
        const max = Math.max(1, ...rows.map(r => r.count));
        host.innerHTML = rows.map(r => `
            <div class="rejection-bar-row">
                <div class="rejection-bar-header"><span>${esc(r.label)}</span><span class="font-mono">${fmtNum(r.count)}</span></div>
                <div class="rejection-bar-track"><div class="rejection-bar-fill" style="width:${Math.round(r.count / max * 100)}%"></div></div>
            </div>`).join('');
    }

    async function fetchRecentBlocks() {
        try {
            const res = await fetch('/api/chain-strip');
            const data = await res.json();
            if (!data.online) return;
            const tip = data.tip_height;
            if (lastTipHeight != null && tip != null && tip > lastTipHeight && sceneReady) {
                triggerMineAnimation();
            }
            if (tip != null) lastTipHeight = tip;
            tipBadge.textContent = `Tip: ${fmtNum(tip)}`;
            const blocks = (data.blocks || []).slice().sort((a, b) => b.height - a.height);
            blocksStrip.innerHTML = blocks.map(b => `
                <div class="explorer-block-card" data-hash="${esc(b.hash)}">
                    <div class="ebc-height font-mono">#${fmtNum(b.height)}</div>
                    <div class="ebc-meta">${fmtNum(b.n_tx)} txs</div>
                    <div class="ebc-meta">${fmtAge(b.time)}</div>
                    ${b.miner_tag ? `<div class="ebc-miner">${esc(b.miner_tag)}</div>` : ''}
                    ${b.policy_fail > 0 ? `<div class="ebc-flag">⚠ ${b.policy_fail} policy fails</div>` : '<div class="ebc-flag ebc-clean">✓ clean</div>'}
                </div>`).join('') || '<p class="text-secondary text-center py-4">No recent block data.</p>';
            blocksStrip.querySelectorAll('[data-hash]').forEach(el =>
                el.addEventListener('click', () => openBlockDetail(el.dataset.hash)));
        } catch (e) { /* transient */ }
    }

    // =====================================================================
    // Detail drawer
    // =====================================================================
    function openDrawer(title) {
        drawerTitle.textContent = title;
        drawerBody.innerHTML = '<p class="text-secondary text-center py-4">Loading…</p>';
        drawer.classList.remove('hidden');
        requestAnimationFrame(() => drawer.classList.add('open'));
    }
    function closeDrawer() {
        drawer.classList.remove('open');
        setTimeout(() => drawer.classList.add('hidden'), 250);
    }

    async function openTxDetail(txid, blockhash) {
        openDrawer('Transaction');
        try {
            const url = `/api/explorer/tx/${encodeURIComponent(txid)}` +
                        (blockhash ? `?blockhash=${encodeURIComponent(blockhash)}` : '');
            const res = await fetch(url);
            const data = await res.json();
            if (!data.success) {
                drawerBody.innerHTML = `<p class="text-secondary py-4">${esc(data.error)}</p>` +
                    (data.needs_txindex ? '<p class="text-secondary">Enable txindex from the banner above to look up any confirmed transaction.</p>' : '');
                return;
            }
            const t = data.tx;
            const ins = t.inputs.map(i => i.coinbase
                ? '<div class="ex-io-row"><span class="badge badge-accent">COINBASE</span></div>'
                : `<div class="ex-io-row">
                       <a class="ex-link font-mono" data-tx="${esc(i.txid)}">${esc(shortId(i.txid, 8))}</a>
                       <span>${i.address ? `<span class="font-mono">${esc(shortId(i.address, 8))}</span>` : ''}</span>
                       <span class="font-mono">${i.value != null ? fmtBtc(i.value) : '—'}</span>
                   </div>`).join('');
            const outs = t.outputs.map(o => `
                <div class="ex-io-row">
                    <span class="text-secondary">#${o.n}</span>
                    <span>${o.address ? `<a class="ex-link font-mono" data-addr="${esc(o.address)}">${esc(shortId(o.address, 8))}</a>` : `<span class="text-muted">${esc(o.type || 'nonstandard')}</span>`}</span>
                    <span class="font-mono">${fmtBtc(o.value)}</span>
                </div>`).join('');
            drawerBody.innerHTML = `
                <div class="ex-kv"><span>Txid</span><span class="font-mono ex-break">${esc(t.txid)}</span></div>
                <div class="ex-kv"><span>Status</span><span>${t.confirmed
                    ? `<span class="badge badge-success">Confirmed · ${fmtNum(t.confirmations)} conf</span>`
                    : '<span class="badge badge-accent">In mempool</span>'}</span></div>
                ${t.blockhash ? `<div class="ex-kv"><span>Block</span><a class="ex-link font-mono" data-block="${esc(t.blockhash)}">${esc(shortId(t.blockhash, 10))}</a></div>` : ''}
                <div class="ex-kv"><span>Size</span><span class="font-mono">${fmtNum(t.vsize)} vB (${fmtNum(t.weight)} WU)</span></div>
                <div class="ex-kv"><span>Fee</span><span class="font-mono">${t.fee_sat != null ? `${fmtNum(t.fee_sat)} sat${t.feerate_satvb ? ` · ${t.feerate_satvb} sat/vB` : ''}` : '—'}</span></div>
                <div class="ex-kv"><span>Total out</span><span class="font-mono">${fmtBtc(t.total_out_btc)}</span></div>
                ${t.mempool_entry ? `<div class="ex-kv"><span>Seen</span><span>${fmtAge(t.mempool_entry.time)} · ${t.mempool_entry.ancestorcount} ancestors</span></div>` : ''}
                ${t.policy_verdict ? `<div class="ex-kv"><span>Policy</span><span class="font-mono">${esc(JSON.stringify(t.policy_verdict))}</span></div>` : ''}
                <h4 class="ex-section">Inputs (${t.inputs.length}${t.inputs_truncated ? ', truncated' : ''})</h4>${ins}
                <h4 class="ex-section">Outputs (${t.outputs.length})</h4>${outs}`;
            wireDrawerLinks();
        } catch (e) {
            drawerBody.innerHTML = '<p class="text-secondary py-4">Failed to load transaction.</p>';
        }
    }

    async function openBlockDetail(hashOrHeight, page) {
        page = page || 0;
        openDrawer('Block');
        try {
            const res = await fetch(`/api/explorer/block/${encodeURIComponent(hashOrHeight)}?page=${page}`);
            const data = await res.json();
            if (!data.success) {
                drawerBody.innerHTML = `<p class="text-secondary py-4">${esc(data.error)}</p>`;
                return;
            }
            const b = data.block, p = data.policy;
            const txRows = data.txs.map(t => `
                <div class="ex-io-row">
                    <a class="ex-link font-mono" data-tx="${esc(t.txid)}" data-bh="${esc(b.hash)}">${esc(shortId(t.txid, 10))}</a>
                    <span>${t.is_coinbase ? '<span class="badge badge-accent">coinbase</span>' : `${fmtNum(t.vsize)} vB`}</span>
                    <span class="font-mono">${t.total_out_btc != null ? fmtBtc(t.total_out_btc) : ''}</span>
                </div>`).join('');
            const nav = `
                <div class="ex-pager">
                    <button class="btn btn-secondary btn-sm" id="ex-page-prev" ${page <= 0 ? 'disabled' : ''}>‹ Prev</button>
                    <span class="text-secondary">Page ${page + 1} / ${fmtNum(data.total_pages)}</span>
                    <button class="btn btn-secondary btn-sm" id="ex-page-next" ${page + 1 >= data.total_pages ? 'disabled' : ''}>Next ›</button>
                </div>`;
            drawerBody.innerHTML = `
                <div class="ex-kv"><span>Height</span><span class="font-mono">#${fmtNum(b.height)}</span></div>
                <div class="ex-kv"><span>Hash</span><span class="font-mono ex-break">${esc(b.hash)}</span></div>
                <div class="ex-kv"><span>Time</span><span>${b.time ? new Date(b.time * 1000).toLocaleString() : '—'} (${fmtAge(b.time)})</span></div>
                <div class="ex-kv"><span>Transactions</span><span class="font-mono">${fmtNum(b.n_tx)}</span></div>
                <div class="ex-kv"><span>Size / weight</span><span class="font-mono">${fmtNum(b.size)} B · ${fmtNum(b.weight)} WU</span></div>
                <div class="ex-kv"><span>Confirmations</span><span class="font-mono">${fmtNum(b.confirmations)}</span></div>
                ${p ? `<div class="ex-kv"><span>Policy audit</span><span>${p.policy_fail > 0
                        ? `<span class="badge badge-danger">${p.policy_fail} of ${fmtNum(p.n_tx)} txs violate policy (${p.policy_fail_pct}%)</span>`
                        : '<span class="badge badge-success">Clean — all txs pass your policy</span>'}
                    ${p.bip110_compliant === false ? ' <span class="badge badge-danger">BIP-110 fail</span>' : ''}</span></div>
                   ${p.miner_tag ? `<div class="ex-kv"><span>Miner</span><span>${esc(p.miner_tag)}</span></div>` : ''}
                   ${p.fees != null ? `<div class="ex-kv"><span>Fees</span><span class="font-mono">${esc(String(p.fees))} BTC</span></div>` : ''}` : ''}
                ${b.previousblockhash ? `<div class="ex-kv"><span>Prev</span><a class="ex-link font-mono" data-block="${esc(b.previousblockhash)}">${esc(shortId(b.previousblockhash, 10))}</a></div>` : ''}
                ${b.nextblockhash ? `<div class="ex-kv"><span>Next</span><a class="ex-link font-mono" data-block="${esc(b.nextblockhash)}">${esc(shortId(b.nextblockhash, 10))}</a></div>` : ''}
                <h4 class="ex-section">Transactions</h4>${txRows}${nav}`;
            const prev = $('ex-page-prev'), next = $('ex-page-next');
            if (prev) prev.addEventListener('click', () => openBlockDetail(b.hash, page - 1));
            if (next) next.addEventListener('click', () => openBlockDetail(b.hash, page + 1));
            wireDrawerLinks();
        } catch (e) {
            drawerBody.innerHTML = '<p class="text-secondary py-4">Failed to load block.</p>';
        }
    }

    let addrPollTimer = null;
    async function openAddressDetail(address) {
        openDrawer('Address');
        drawerBody.innerHTML = `
            <div class="ex-kv"><span>Address</span><span class="font-mono ex-break">${esc(address)}</span></div>
            <p class="text-secondary mt-2">Scanning the UTXO set for current unspent outputs. This takes a minute or two — the Oracle is combing the entire chainstate.</p>
            <div class="scan-progress"><div class="scan-progress-fill" id="scan-progress-fill" style="width:2%"></div></div>
            <p class="text-secondary" id="scan-progress-label">Starting…</p>
            <button class="btn btn-secondary btn-sm" id="scan-abort-btn">Cancel scan</button>`;
        const abortBtn = $('scan-abort-btn');
        if (abortBtn) abortBtn.addEventListener('click', async () => {
            await fetch('/api/explorer/address/abort', { method: 'POST' });
            stopAddrPoll();
            drawerBody.innerHTML = '<p class="text-secondary py-4">Scan cancelled.</p>';
        });
        try {
            const res = await fetch('/api/explorer/address/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address }),
            });
            const data = await res.json();
            if (res.status === 409) {
                drawerBody.innerHTML = `<p class="text-secondary py-4">Another scan is already running (${esc(shortId(data.in_flight, 8))}). Try again shortly.</p>`;
                return;
            }
            if (!data.success) {
                drawerBody.innerHTML = `<p class="text-secondary py-4">${esc(data.error)}</p>`;
                return;
            }
            if (data.cached) { renderAddressResult(data.result); return; }
            addrPollTimer = setInterval(pollAddressStatus, 2000);
        } catch (e) {
            drawerBody.innerHTML = '<p class="text-secondary py-4">Failed to start scan.</p>';
        }
    }

    function stopAddrPoll() {
        if (addrPollTimer) { clearInterval(addrPollTimer); addrPollTimer = null; }
    }

    async function pollAddressStatus() {
        try {
            const res = await fetch('/api/explorer/address/status');
            const data = await res.json();
            if (!data.done) {
                const pct = Math.max(2, Math.round(data.progress || 0));
                const fill = $('scan-progress-fill'), label = $('scan-progress-label');
                if (fill) fill.style.width = `${pct}%`;
                if (label) label.textContent = `Scanning UTXO set… ${pct}%`;
                return;
            }
            stopAddrPoll();
            if (data.success && data.result) renderAddressResult(data.result);
            else drawerBody.innerHTML = `<p class="text-secondary py-4">${esc(data.error || 'Scan failed.')}</p>`;
        } catch (e) { /* keep polling */ }
    }

    function renderAddressResult(r) {
        const rows = (r.utxos || []).map(u => `
            <div class="ex-io-row">
                <a class="ex-link font-mono" data-tx="${esc(u.txid)}">${esc(shortId(u.txid, 8))}:${u.vout}</a>
                <span class="text-secondary">height ${fmtNum(u.height)}</span>
                <span class="font-mono">${fmtBtc(u.amount)}</span>
            </div>`).join('');
        drawerBody.innerHTML = `
            <div class="ex-kv"><span>Address</span><span class="font-mono ex-break">${esc(r.address)}</span></div>
            <div class="ex-kv"><span>Current balance</span><span class="font-mono">${fmtBtc(r.total_amount || 0)}</span></div>
            <div class="ex-kv"><span>UTXOs</span><span class="font-mono">${fmtNum(r.utxo_count)}</span></div>
            <p class="text-secondary text-xs mt-2">Snapshot of unspent outputs at height ${fmtNum(r.height)}. Full address history requires an external indexer.</p>
            ${rows ? `<h4 class="ex-section">Unspent outputs</h4>${rows}` : '<p class="text-secondary py-4">No unspent outputs found for this address.</p>'}`;
        wireDrawerLinks();
    }

    function wireDrawerLinks() {
        drawerBody.querySelectorAll('[data-tx]').forEach(el =>
            el.addEventListener('click', () => openTxDetail(el.dataset.tx, el.dataset.bh)));
        drawerBody.querySelectorAll('[data-block]').forEach(el =>
            el.addEventListener('click', () => openBlockDetail(el.dataset.block)));
        drawerBody.querySelectorAll('[data-addr]').forEach(el =>
            el.addEventListener('click', () => openAddressDetail(el.dataset.addr)));
    }

    // =====================================================================
    // Search
    // =====================================================================
    async function doSearch() {
        const q = (searchInput.value || '').trim();
        searchError.classList.add('hidden');
        if (!q) return;
        try {
            const res = await fetch(`/api/explorer/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            if (!data.success) {
                searchError.textContent = data.error || 'Not found.';
                searchError.classList.remove('hidden');
                return;
            }
            if (data.type === 'block') openBlockDetail(data.target);
            else if (data.type === 'tx') openTxDetail(data.target);
            else if (data.type === 'address') openAddressDetail(data.target);
        } catch (e) {
            searchError.textContent = 'Search failed — is the node running?';
            searchError.classList.remove('hidden');
        }
    }

    // =====================================================================
    // txindex banner / enable flow
    // =====================================================================
    async function checkCapabilities() {
        try {
            const res = await fetch('/api/explorer/capabilities');
            capabilities = await res.json();
            if (!capabilities.online) { txBanner.classList.add('hidden'); return; }
            const tx = capabilities.txindex || {};
            if (tx.available && tx.synced) {
                txBanner.classList.add('hidden');
            } else if (tx.available && !tx.synced) {
                txBanner.classList.remove('hidden');
                txBannerDetail.textContent = `txindex is building: ${tx.progress}% — transaction lookup will unlock when it completes.`;
                txBannerBtn.classList.add('hidden');
                setTimeout(checkCapabilities, 15000);
            } else {
                txBanner.classList.remove('hidden');
                txBannerBtn.classList.remove('hidden');
            }
        } catch (e) { /* transient */ }
    }

    async function enableTxindex() {
        const ok = window.confirm(
            'Enable txindex?\n\nThis writes txindex=1 to bitcoin.conf and restarts the node. ' +
            'Building the index takes a while (the node keeps working meanwhile) and uses extra disk space (~60 GB on mainnet).');
        if (!ok) return;
        txBannerBtn.disabled = true;
        txBannerDetail.textContent = 'Saving configuration and restarting the node…';
        try {
            const save = await fetch('/api/config/parsed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ txindex: 1 }),
            });
            const saved = await save.json();
            if (saved && saved.success === false) throw new Error(saved.error || 'config save failed');
            await fetch('/api/stop', { method: 'POST' });
            await new Promise(r => setTimeout(r, 4000));
            await fetch('/api/start', { method: 'POST' });
            txBannerDetail.textContent = 'Node restarting with txindex=1 — index build progress will appear here.';
            setTimeout(checkCapabilities, 15000);
        } catch (e) {
            txBannerDetail.textContent = 'Failed to enable txindex automatically. Add txindex=1 in Configuration and restart the node.';
        } finally {
            txBannerBtn.disabled = false;
        }
    }

    // =====================================================================
    // Lifecycle
    // =====================================================================
    function initDom() {
        if (inited) return;
        inited = true;
        searchInput = $('explorer-search-input'); searchBtn = $('explorer-search-btn');
        searchError = $('explorer-search-error');
        txBanner = $('explorer-txindex-banner'); txBannerDetail = $('explorer-txindex-detail');
        txBannerBtn = $('explorer-txindex-enable');
        hudTxCount = $('hud-tx-count'); hudVsize = $('hud-vsize'); hudMinFee = $('hud-minfee');
        canvasWrap = $('explorer-canvas-wrap'); canvas = $('mempool-3d');
        tooltip = $('explorer-tooltip'); webglFallback = $('explorer-webgl-fallback');
        projectedStrip = $('projected-blocks-strip'); blocksStrip = $('explorer-blocks-strip');
        tipBadge = $('explorer-tip-height');
        drawer = $('explorer-drawer'); drawerTitle = $('explorer-drawer-title');
        drawerBody = $('explorer-drawer-body');

        searchBtn.addEventListener('click', doSearch);
        searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });
        $('explorer-drawer-close').addEventListener('click', () => { stopAddrPoll(); closeDrawer(); });
        txBannerBtn.addEventListener('click', enableTxindex);

        const bipToggle = $('explorer-bip110-toggle');
        const bipPanel = $('panel-bip110');
        if (bipToggle && bipPanel) bipToggle.addEventListener('click', () =>
            bipPanel.classList.toggle('explorer-bip110-collapsed'));

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) stopLoop();
            else if (visible) startLoop();
        });
    }

    function startPolling() {
        stopPolling();
        fetchMempool();
        fetchRecentBlocks();
        pollTimer = setInterval(() => { fetchMempool(); fetchRecentBlocks(); }, POLL_MS);
    }
    function stopPolling() {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }

    window.OracleExplorer = {
        onTabShow(running) {
            initDom();
            visible = true;
            nodeRunning = !!running;
            if (initScene()) { resizeRenderer(); startLoop(); }
            checkCapabilities();
            startPolling();
        },
        onTabHide() {
            if (!visible) return;
            visible = false;
            stopPolling();
            stopAddrPoll();
            stopLoop();
        },
        refresh() {
            if (visible && !pollTimer) startPolling();
        },
    };
})();
