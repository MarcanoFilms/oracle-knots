// Copyright (c) 2026 The Oracle Knots developers
// Operator RPCs: sovereign mining stats, diagnostics, mempool policy audit.

#include <chain.h>
#include <chainparams.h>
#include <common/args.h>
#include <consensus/tx_verify.h>
#include <consensus/validation.h>
#include <node/blockstorage.h>
#include <core_io.h>
#include <deploymentinfo.h>
#include <deploymentstatus.h>
#include <node/context.h>
#include <node/miner.h>
#include <policy/oracle_policy.h>
#include <policy/policy.h>
#include <rpc/server.h>
#include <rpc/server_util.h>
#include <rpc/util.h>
#include <txmempool.h>
#include <util/strencodings.h>
#include <validation.h>

using node::BlockAssembler;
using node::BlockManager;
using node::NodeContext;

static UniValue TemplateStatsToJSON()
{
    const auto& s = OraclePolicy::g_last_template_stats;
    UniValue obj(UniValue::VOBJ);
    obj.pushKV("txs_included", s.txs_included);
    obj.pushKV("mempool_size_at_template", s.mempool_size);
    obj.pushKV("policy_filtered", s.policy_filtered);
    obj.pushKV("fees", s.fees);
    obj.pushKV("weight", s.weight);
    obj.pushKV("assembly_ms", s.assembly_ms);
    obj.pushKV("profile", s.profile);
    obj.pushKV("timestamp", s.timestamp);
    if (s.mempool_size > 0) {
        const double filter_pct = (static_cast<double>(s.policy_filtered) /
            (static_cast<double>(s.txs_included) + static_cast<double>(s.policy_filtered))) * 100.0;
        obj.pushKV("template_filter_rate_pct", filter_pct);
    } else {
        obj.pushKV("template_filter_rate_pct", 0.0);
    }
    if (BlockAssembler::m_last_block_num_txs) {
        obj.pushKV("currentblocktx", *BlockAssembler::m_last_block_num_txs);
    }
    if (BlockAssembler::m_last_block_weight) {
        obj.pushKV("currentblockweight", *BlockAssembler::m_last_block_weight);
    }
    if (BlockAssembler::m_last_block_fees) {
        obj.pushKV("currentblockfees", *BlockAssembler::m_last_block_fees);
    }
    return obj;
}

static RPCHelpMan getsovereigntemplatestats()
{
    return RPCHelpMan{"getsovereigntemplatestats",
        "\nReturns sovereign block template statistics from the last assembly.\n"
        "Useful for monitoring policy-filtered mining templates (works in pruned mode).\n",
        {},
        RPCResult{RPCResult::Type::OBJ, "", ""},
        RPCExamples{
            HelpExampleCli("getsovereigntemplatestats", "")
            + HelpExampleRpc("getsovereigntemplatestats", "")},
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue {
            UniValue result = TemplateStatsToJSON();
            result.pushKV("bip110_mode", OraclePolicy::g_bip110_mode);
            result.pushKV("active_policy_profile", OraclePolicy::g_active_profile);
            return result;
        }};
}

static void PushDiagnostic(UniValue& arr, const std::string& id, const std::string& severity,
                          const std::string& message, const std::string& recommendation = "")
{
    UniValue item(UniValue::VOBJ);
    item.pushKV("id", id);
    item.pushKV("severity", severity);
    item.pushKV("message", message);
    if (!recommendation.empty()) item.pushKV("recommendation", recommendation);
    arr.push_back(std::move(item));
}

static RPCHelpMan getsovereigndiagnostics()
{
    return RPCHelpMan{"getsovereigndiagnostics",
        "\nOperator preflight: checks policy, privacy, sync, and mining readiness.\n",
        {},
        RPCResult{RPCResult::Type::OBJ, "", ""},
        RPCExamples{
            HelpExampleCli("getsovereigndiagnostics", "")
            + HelpExampleRpc("getsovereigndiagnostics", "")},
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue {
            NodeContext& node = EnsureAnyNodeContext(request.context);
            ChainstateManager& chainman = EnsureChainman(node);
            const CTxMemPool& mempool = EnsureMemPool(node);

            UniValue checks(UniValue::VARR);
            LOCK(cs_main);
            const CBlockIndex* tip = chainman.ActiveChain().Tip();

            PushDiagnostic(checks, "policy_profile", "info",
                strprintf("Active policy profile: %s (BIP-110 mode: %s)",
                    OraclePolicy::g_active_profile, OraclePolicy::g_bip110_mode));

            if (OraclePolicy::g_active_profile == "maximalist" || OraclePolicy::g_active_profile == "monetary-only") {
                PushDiagnostic(checks, "policy_strict", "info",
                    "Strict sovereign policy active — non-monetary transactions are filtered.",
                    "Ideal for sovereign mining with spam-free block templates.");
            }

            const bool has_proxy = gArgs.IsArgSet("-proxy") || gArgs.IsArgSet("-onion");
            if (!has_proxy && chainman.GetParams().GetChainType() == ChainType::MAIN) {
                PushDiagnostic(checks, "privacy_tor", "warning",
                    "No Tor/I2P proxy configured on mainnet.",
                    "Set proxy=127.0.0.1:9050 and onion=127.0.0.1:9050 in bitcoin.conf for better privacy.");
            } else if (has_proxy) {
                PushDiagnostic(checks, "privacy_tor", "info", "Privacy proxy configured.");
            }

            if (tip && chainman.IsInitialBlockDownload()) {
                PushDiagnostic(checks, "sync_ibd", "warning",
                    "Node is still syncing (initial block download).",
                    "Wait for full sync before relying on template stats for mining.");
            } else if (tip) {
                PushDiagnostic(checks, "sync_ibd", "info", "Node is synced.");
            }

            if (gArgs.GetBoolArg("-prune", false)) {
                PushDiagnostic(checks, "prune_mode", "info",
                    "Pruned mode enabled — mempool policy audit and templates still work; txindex is not required.");
            }

            if (gArgs.IsArgSet("-policyprofile") && gArgs.GetArg("-policyprofile", "") != OraclePolicy::g_active_profile) {
                PushDiagnostic(checks, "policy_cli_override", "warning",
                    strprintf("CLI -policyprofile=%s may override policy.toml on restart.",
                        gArgs.GetArg("-policyprofile", "")),
                    "Align bitcoin.conf policyprofile with policy.toml or remove the CLI override.");
            }

            const uint64_t reject_total = OraclePolicy::g_rejection_counts.count("total")
                ? OraclePolicy::g_rejection_counts.at("total") : 0;
            if (reject_total > 0) {
                PushDiagnostic(checks, "rejections_active", "info",
                    strprintf("%llu transactions rejected by policy since startup.", reject_total),
                    "Review Dashboard rejections or debug.log lines prefixed with 'Oracle Policy'.");
            }

            UniValue result(UniValue::VOBJ);
            result.pushKV("checks", std::move(checks));
            result.pushKV("mempool_size", static_cast<uint64_t>(mempool.size()));
            result.pushKV("template_stats", TemplateStatsToJSON());
            return result;
        }};
}

static std::string NormalizeReasonKey(const std::string& reason)
{
    return reason.empty() ? "policy" : reason;
}

static int ParseBoundedIntArg(const UniValue& val, int default_val, int min_val, int max_val)
{
    if (val.isNull()) return default_val;
    int parsed = default_val;
    if (val.isNum()) {
        parsed = val.getInt<int>();
    } else if (val.isStr()) {
        if (!ParseInt32(val.get_str(), &parsed)) {
            throw JSONRPCError(RPC_TYPE_ERROR, "Invalid integer argument");
        }
    } else {
        throw JSONRPCError(RPC_TYPE_ERROR, "Invalid integer argument");
    }
    return std::min(max_val, std::max(min_val, parsed));
}

static RPCHelpMan getmempoolpolicyaudit()
{
    return RPCHelpMan{"getmempoolpolicyaudit",
        "\nAudit in-memory mempool transactions against the active sovereign policy.\n"
        "Does not require txindex; safe in pruned mode.\n",
        {
            {"limit", RPCArg::Type::NUM, RPCArg::Default{500},
                "Maximum transactions to scan (0 = entire mempool)"},
        },
        RPCResult{RPCResult::Type::OBJ, "", ""},
        RPCExamples{
            HelpExampleCli("getmempoolpolicyaudit", "200")
            + HelpExampleRpc("getmempoolpolicyaudit", "200")},
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue {
            NodeContext& node = EnsureAnyNodeContext(request.context);
            const CTxMemPool& mempool = EnsureMemPool(node);

            int limit = 500;
            if (request.params.size() > 0) {
                limit = request.params[0].getInt<int>();
            }

            uint64_t pass_count = 0;
            uint64_t fail_count = 0;
            uint64_t scanned = 0;
            std::map<std::string, uint64_t> fail_by_reason;
            UniValue samples(UniValue::VARR);

            LOCK(mempool.cs);
            const size_t max_scan = limit <= 0 ? mempool.size() : static_cast<size_t>(limit);
            for (auto it = mempool.mapTx.begin(); it != mempool.mapTx.end() && scanned < max_scan; ++it, ++scanned) {
                std::string reason;
                if (IsStandardTx(it->GetTx(), mempool.m_opts, reason, empty_ignore_rejects, /*record_rejections=*/false)) {
                    pass_count++;
                } else {
                    fail_count++;
                    const std::string key = NormalizeReasonKey(reason);
                    fail_by_reason[key]++;
                    if (samples.size() < 15) {
                        UniValue sample(UniValue::VOBJ);
                        sample.pushKV("txid", it->GetTx().GetHash().GetHex());
                        sample.pushKV("wtxid", it->GetTx().GetWitnessHash().GetHex());
                        sample.pushKV("reason", key);
                        sample.pushKV("message", OraclePolicy::RejectReasonToMessage(key));
                        samples.push_back(std::move(sample));
                    }
                }
            }

            UniValue failures(UniValue::VOBJ);
            for (const auto& entry : fail_by_reason) {
                failures.pushKV(entry.first, entry.second);
            }

            const uint64_t total = pass_count + fail_count;
            UniValue result(UniValue::VOBJ);
            result.pushKV("scanned", scanned);
            result.pushKV("mempool_total", static_cast<uint64_t>(mempool.size()));
            result.pushKV("would_pass", pass_count);
            result.pushKV("would_fail", fail_count);
            result.pushKV("pass_rate_pct", total > 0 ? (static_cast<double>(pass_count) / total) * 100.0 : 100.0);
            result.pushKV("failures_by_reason", std::move(failures));
            result.pushKV("sample_failures", std::move(samples));
            result.pushKV("active_policy_profile", OraclePolicy::g_active_profile);
            return result;
        }};
}

static void AuditBlockPolicy(const CBlock& block, const kernel::MemPoolOptions& opts,
                             uint64_t& policy_pass, uint64_t& policy_fail, bool& bip110_compliant)
{
    policy_pass = 0;
    policy_fail = 0;
    bip110_compliant = true;
    for (const CTransactionRef& tx : block.vtx) {
        TxValidationState tx_state;
        if (!Consensus::CheckOutputSizes(*tx, tx_state)) {
            bip110_compliant = false;
        }
        std::string reason;
        if (IsStandardTx(*tx, opts, reason, empty_ignore_rejects, /*record_rejections=*/false)) {
            policy_pass++;
        } else {
            policy_fail++;
        }
    }
}

static bool BlockDataAvailable(BlockManager& blockman, const CBlockIndex& index)
{
    if (!(index.nStatus & BLOCK_HAVE_DATA)) {
        return false;
    }
    return !blockman.IsBlockPruned(index);
}

static std::string ExtractCoinbaseMinerTag(const CBlock& block)
{
    if (block.vtx.empty() || block.vtx[0]->vin.empty()) return "Unknown";
    const std::vector<unsigned char> script(block.vtx[0]->vin[0].scriptSig.begin(), block.vtx[0]->vin[0].scriptSig.end());
    std::string best;
    std::string current;
    for (unsigned char c : script) {
        if (c >= 0x20 && c <= 0x7e) {
            current += static_cast<char>(c);
        } else {
            if (current.size() >= 3 && current.size() > best.size()) {
                best = current;
            }
            current.clear();
        }
    }
    if (current.size() >= 3 && current.size() > best.size()) {
        best = current;
    }
    if (best.empty()) return "Unknown";
    if (best.size() > 64) best.resize(64);
    return best;
}

static void PushCoinbaseEconomics(UniValue& item, const CBlock& block, int height, const Consensus::Params& consensus)
{
    if (block.vtx.empty()) return;
    CAmount coinbase_value{0};
    for (const auto& out : block.vtx[0]->vout) {
        coinbase_value += out.nValue;
    }
    const CAmount subsidy = GetBlockSubsidy(height, consensus);
    const CAmount fees = coinbase_value - subsidy;
    item.pushKV("subsidy", ValueFromAmount(subsidy));
    item.pushKV("fees", ValueFromAmount(fees));
    item.pushKV("coinbase_reward", ValueFromAmount(coinbase_value));
    item.pushKV("fees_sats", fees);
    item.pushKV("miner_tag", ExtractCoinbaseMinerTag(block));
}

static RPCHelpMan getrecentblockpolicyaudit()
{
    return RPCHelpMan{"getrecentblockpolicyaudit",
        "\nAudit the most recent blocks against sovereign policy and BIP-110 output limits.\n"
        "Works in pruned mode for blocks still on disk (typically the chain tip window).\n",
        {
            {"count", RPCArg::Type::NUM, RPCArg::Default{12},
                "Number of recent blocks to audit (1-24, oldest to newest)"},
        },
        RPCResult{RPCResult::Type::OBJ, "", "",
            {
                {RPCResult::Type::ARR, "blocks", "Blocks from oldest to newest",
                    {
                        {RPCResult::Type::OBJ, "", "",
                            {
                                {RPCResult::Type::NUM, "height", "Block height"},
                                {RPCResult::Type::STR_HEX, "hash", "Block hash"},
                                {RPCResult::Type::NUM, "time", "Block time (unix)"},
                                {RPCResult::Type::NUM, "n_tx", "Transaction count"},
                                {RPCResult::Type::BOOL, "available", "Whether full block data was read"},
                                {RPCResult::Type::BOOL, "bip110_compliant", "BIP-110 output size compliance"},
                                {RPCResult::Type::NUM, "policy_pass", "Transactions passing sovereign policy"},
                                {RPCResult::Type::NUM, "policy_fail", "Transactions failing sovereign policy"},
                                {RPCResult::Type::BOOL, "policy_clean", "True when policy_fail is 0"},
                                {RPCResult::Type::STR_AMOUNT, "subsidy", "Block subsidy (coinbase minus fees)"},
                                {RPCResult::Type::STR_AMOUNT, "fees", "Total transaction fees in coinbase"},
                                {RPCResult::Type::STR_AMOUNT, "coinbase_reward", "Total coinbase output value"},
                                {RPCResult::Type::NUM, "fees_sats", "Fees in satoshis"},
                                {RPCResult::Type::STR, "miner_tag", "Miner/pool tag from coinbase scriptSig"},
                            }},
                    }},
                {RPCResult::Type::NUM, "tip_height", "Current chain tip height"},
                {RPCResult::Type::STR, "active_policy_profile", "Active policy profile"},
            }},
        RPCExamples{
            HelpExampleCli("getrecentblockpolicyaudit", "12")
            + HelpExampleRpc("getrecentblockpolicyaudit", "12")},
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue {
            NodeContext& node = EnsureAnyNodeContext(request.context);
            ChainstateManager& chainman = EnsureChainman(node);
            const CTxMemPool& mempool = EnsureMemPool(node);

            const int count = request.params.size() > 0
                ? ParseBoundedIntArg(request.params[0], 12, 1, 24)
                : 12;

            kernel::MemPoolOptions opts;
            {
                LOCK(mempool.cs);
                opts = mempool.m_opts;
            }

            UniValue blocks(UniValue::VARR);
            int tip_height = 0;

            LOCK(cs_main);
            const CBlockIndex* tip = chainman.ActiveChain().Tip();
            if (!tip) {
                UniValue result(UniValue::VOBJ);
                result.pushKV("blocks", std::move(blocks));
                result.pushKV("tip_height", 0);
                result.pushKV("active_policy_profile", OraclePolicy::g_active_profile);
                return result;
            }

            tip_height = tip->nHeight;
            const int start_height = std::max(0, tip_height - count + 1);

            for (int height = start_height; height <= tip_height; ++height) {
                const CBlockIndex* pindex = chainman.ActiveChain()[height];
                if (!pindex) continue;

                UniValue item(UniValue::VOBJ);
                item.pushKV("height", pindex->nHeight);
                item.pushKV("hash", pindex->GetBlockHash().GetHex());
                item.pushKV("time", pindex->GetBlockTime());
                item.pushKV("n_tx", static_cast<uint64_t>(pindex->nTx));

                if (!BlockDataAvailable(chainman.m_blockman, *pindex)) {
                    item.pushKV("available", false);
                    item.pushKV("bip110_compliant", UniValue());
                    item.pushKV("policy_pass", UniValue());
                    item.pushKV("policy_fail", UniValue());
                    item.pushKV("policy_clean", UniValue());
                    blocks.push_back(std::move(item));
                    continue;
                }

                CBlock block;
                if (!chainman.m_blockman.ReadBlock(block, *pindex)) {
                    item.pushKV("available", false);
                    item.pushKV("bip110_compliant", UniValue());
                    item.pushKV("policy_pass", UniValue());
                    item.pushKV("policy_fail", UniValue());
                    item.pushKV("policy_clean", UniValue());
                    blocks.push_back(std::move(item));
                    continue;
                }

                uint64_t policy_pass = 0;
                uint64_t policy_fail = 0;
                bool bip110_compliant = true;
                AuditBlockPolicy(block, opts, policy_pass, policy_fail, bip110_compliant);

                item.pushKV("available", true);
                item.pushKV("bip110_compliant", bip110_compliant);
                item.pushKV("policy_pass", policy_pass);
                item.pushKV("policy_fail", policy_fail);
                item.pushKV("policy_clean", policy_fail == 0);
                PushCoinbaseEconomics(item, block, pindex->nHeight, chainman.GetParams().GetConsensus());
                blocks.push_back(std::move(item));
            }

            UniValue result(UniValue::VOBJ);
            result.pushKV("blocks", std::move(blocks));
            result.pushKV("tip_height", tip_height);
            result.pushKV("active_policy_profile", OraclePolicy::g_active_profile);
            return result;
        }};
}

static RPCHelpMan getrecentpolicyrejections()
{
    return RPCHelpMan{"getrecentpolicyrejections",
        "\nReturn recent policy rejections from the in-memory ring buffer.\n",
        {
            {"limit", RPCArg::Type::NUM, RPCArg::Default{50}, "Max entries (max 100)"},
        },
        RPCResult{RPCResult::Type::ARR, "", "", {
            {RPCResult::Type::OBJ, "", "Recent policy rejection",
                {
                    {RPCResult::Type::STR, "reason", "Machine-readable rejection reason"},
                    {RPCResult::Type::STR, "message", "Human-readable rejection message"},
                    {RPCResult::Type::STR, "wtxid", "Witness transaction id"},
                    {RPCResult::Type::STR, "context", "Where rejected (relay, template, mempool)"},
                    {RPCResult::Type::NUM, "timestamp", "Unix timestamp"},
                }},
        }},
        RPCExamples{
            HelpExampleCli("getrecentpolicyrejections", "20")
            + HelpExampleRpc("getrecentpolicyrejections", "20")},
        [&](const RPCHelpMan& self, const JSONRPCRequest& request) -> UniValue {
            int limit = 50;
            if (request.params.size() > 0) {
                limit = std::min(100, std::max(1, request.params[0].getInt<int>()));
            }
            UniValue arr(UniValue::VARR);
            int n = 0;
            for (const auto& entry : OraclePolicy::g_recent_rejections) {
                if (n++ >= limit) break;
                UniValue item(UniValue::VOBJ);
                item.pushKV("reason", entry.reason);
                item.pushKV("message", entry.message);
                item.pushKV("wtxid", entry.wtxid);
                item.pushKV("context", entry.context);
                item.pushKV("timestamp", entry.timestamp);
                arr.push_back(std::move(item));
            }
            return arr;
        }};
}

void RegisterOracleOperatorRPCCommands(CRPCTable& t)
{
    static const CRPCCommand commands[]{
        {"mining", &getsovereigntemplatestats},
        {"util", &getsovereigndiagnostics},
        {"mining", &getmempoolpolicyaudit},
        {"util", &getrecentpolicyrejections},
        {"util", &getrecentblockpolicyaudit},
    };
    for (const auto& c : commands) {
        t.appendCommand(c.name, &c);
    }
}