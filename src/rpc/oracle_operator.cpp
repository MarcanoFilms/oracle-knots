// Copyright (c) 2026 The Oracle Knots developers
// Operator RPCs: sovereign mining stats, diagnostics, mempool policy audit.

#include <chain.h>
#include <chainparams.h>
#include <common/args.h>
#include <consensus/validation.h>
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
    };
    for (const auto& c : commands) {
        t.appendCommand(c.name, &c);
    }
}