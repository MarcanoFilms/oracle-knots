#include <policy/oracle_policy.h>
#include <common/args.h>
#include <util/fs.h>
#include <logging.h>
#include <policy/policy.h>

#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace OraclePolicy {

std::string g_active_profile = "maximalist";
std::string g_bip110_mode = "auto";

int g_max_datacarrier_bytes = 0;
bool g_reject_tokens = true;
bool g_reject_inscriptions = true;
int g_dust_relay_fee = 3000;
bool g_permit_bare_multisig = false;
bool g_permit_bare_pubkey = false;
bool g_reject_parasites = true;
int g_max_op_return_outputs = 0;

int64_t g_startup_time = 0;
std::map<std::string, uint64_t> g_rejection_counts = {
    {"total", 0},
    {"tokens-runes", 0},
    {"tokens-olga", 0},
    {"inscription", 0},
    {"dust-nonanchor", 0},
    {"dust-nonzero", 0},
    {"bare-pubkey", 0},
    {"bare-multisig", 0},
    {"parasite-cat21", 0},
    {"max-op-returns", 0}
};

// Trim helper
static std::string Trim(const std::string& str) {
    auto start = std::find_if_not(str.begin(), str.end(), [](unsigned char ch) {
        return std::isspace(ch);
    });
    auto end = std::find_if_not(str.rbegin(), str.rend(), [](unsigned char ch) {
        return std::isspace(ch);
    }).base();
    return (start < end) ? std::string(start, end) : "";
}

// Inscription detection: search for OP_FALSE (0x00) OP_IF (0x63) 0x03 'o' 'r' 'd' (0x6f 0x72 0x64)
bool HasInscription(const CTransaction& tx) {
    if (!g_reject_inscriptions) return false;

    for (const auto& txin : tx.vin) {
        if (txin.scriptWitness.IsNull()) continue;
        for (const auto& item : txin.scriptWitness.stack) {
            if (item.size() >= 6) {
                for (size_t i = 0; i <= item.size() - 6; ++i) {
                    if (item[i] == 0x00 && item[i+1] == 0x63 && item[i+2] == 0x03 &&
                        item[i+3] == 0x6f && item[i+4] == 0x72 && item[i+5] == 0x64) {
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

bool ExceedsMaxOpReturns(const CTransaction& tx) {
    int op_return_count = 0;
    for (const auto& txout : tx.vout) {
        if (txout.scriptPubKey.size() > 0 && txout.scriptPubKey[0] == OP_RETURN) {
            op_return_count++;
        }
    }
    return op_return_count > g_max_op_return_outputs;
}

void ApplyProfileSettings(const std::string& profile_name, kernel::MemPoolOptions& mempool_opts) {
    if (profile_name == "maximalist") {
        g_max_datacarrier_bytes = 0;
        g_reject_tokens = true;
        g_reject_inscriptions = true;
        g_dust_relay_fee = 3000;
        g_permit_bare_multisig = false;
        g_permit_bare_pubkey = false;
        g_reject_parasites = true;
        g_max_op_return_outputs = 0;
    } else if (profile_name == "bip110-strict") {
        g_max_datacarrier_bytes = 83;
        g_reject_tokens = true;
        g_reject_inscriptions = true;
        g_dust_relay_fee = 3000;
        g_permit_bare_multisig = false;
        g_permit_bare_pubkey = false;
        g_reject_parasites = true;
        g_max_op_return_outputs = 1;
    } else if (profile_name == "monetary-only") {
        g_max_datacarrier_bytes = 0;
        g_reject_tokens = true;
        g_reject_inscriptions = true;
        g_dust_relay_fee = 3000;
        g_permit_bare_multisig = false;
        g_permit_bare_pubkey = false;
        g_reject_parasites = true;
        g_max_op_return_outputs = 0;
    } else if (profile_name == "default-knots") {
        g_max_datacarrier_bytes = 83;
        g_reject_tokens = false;
        g_reject_inscriptions = false;
        g_dust_relay_fee = 3000;
        g_permit_bare_multisig = false;
        g_permit_bare_pubkey = false;
        g_reject_parasites = true;
        g_max_op_return_outputs = 1;
    }

    // Apply to Bitcoin's native mempool options
    mempool_opts.reject_tokens = g_reject_tokens;
    mempool_opts.reject_parasites = g_reject_parasites;
    mempool_opts.permit_bare_pubkey = g_permit_bare_pubkey;
    mempool_opts.permit_bare_multisig = g_permit_bare_multisig;
    if (g_max_datacarrier_bytes > 0) {
        mempool_opts.max_datacarrier_bytes = g_max_datacarrier_bytes;
    } else {
        mempool_opts.max_datacarrier_bytes = std::nullopt;
    }
    mempool_opts.dust_relay_feerate = CFeeRate(g_dust_relay_fee);
}

void LoadPolicyConfig(kernel::MemPoolOptions& mempool_opts) {
    fs::path config_path = gArgs.GetDataDirNet() / "policy.toml";

    // Set startup time if not set
    if (g_startup_time == 0) {
        g_startup_time = GetTime();
    }

    // Check if configuration overrides are set via command line
    bool has_cmd_profile = gArgs.IsArgSet("-policyprofile");
    bool has_cmd_bip110 = gArgs.IsArgSet("-bip110");
    bool has_cmd_reject_insc = gArgs.IsArgSet("-rejectinscriptions");

    if (has_cmd_profile) {
        g_active_profile = gArgs.GetArg("-policyprofile", "maximalist");
        LogPrintf("Oracle Policy: Profile set via CLI to: %s\n", g_active_profile);
    }
    if (has_cmd_bip110) {
        g_bip110_mode = gArgs.GetArg("-bip110", "auto");
        LogPrintf("Oracle Policy: BIP-110 enforcement mode via CLI: %s\n", g_bip110_mode);
    }
    if (has_cmd_reject_insc) {
        g_reject_inscriptions = gArgs.GetBoolArg("-rejectinscriptions", true);
    }

    // Check if policy.toml exists; if not, write a default template
    if (!fs::exists(config_path)) {
        LogPrintf("Oracle Policy: policy.toml not found, creating default configuration at %s\n", fs::PathToString(config_path));
        SavePolicyConfig();
    }

    // Read and parse policy.toml if we aren't overriding everything via CLI
    std::ifstream file(config_path);
    if (file.is_open()) {
        std::string line;
        bool in_custom_rules = false;

        while (std::getline(file, line)) {
            line = Trim(line);
            if (line.empty() || line[0] == '#' || line[0] == ';') continue;

            // Handle sections
            if (line[0] == '[' && line.back() == ']') {
                std::string section = Trim(line.substr(1, line.size() - 2));
                if (section == "custom_rules") {
                    in_custom_rules = true;
                } else {
                    in_custom_rules = false;
                }
                continue;
            }

            // Parse key-value pairs
            size_t eq_pos = line.find('=');
            if (eq_pos == std::string::npos) continue;

            std::string key = Trim(line.substr(0, eq_pos));
            std::string val_str = Trim(line.substr(eq_pos + 1));

            // Strip inline comments in values
            size_t hash_pos = val_str.find('#');
            if (hash_pos != std::string::npos) {
                val_str = Trim(val_str.substr(0, hash_pos));
            }
            size_t semi_pos = val_str.find(';');
            if (semi_pos != std::string::npos) {
                val_str = Trim(val_str.substr(0, semi_pos));
            }

            // Remove quotes if present
            if (val_str.size() >= 2 && val_str.front() == '"' && val_str.back() == '"') {
                val_str = val_str.substr(1, val_str.size() - 2);
            }

            if (!in_custom_rules) {
                if (key == "profile" && !has_cmd_profile) {
                    g_active_profile = val_str;
                } else if (key == "bip110_mode" && !has_cmd_bip110) {
                    g_bip110_mode = val_str;
                }
            } else {
                if (key == "datacarrier_size") {
                    g_max_datacarrier_bytes = std::stoi(val_str);
                } else if (key == "reject_tokens") {
                    g_reject_tokens = (val_str == "true" || val_str == "1");
                } else if (key == "reject_inscriptions" && !has_cmd_reject_insc) {
                    g_reject_inscriptions = (val_str == "true" || val_str == "1");
                } else if (key == "dust_relay_fee") {
                    g_dust_relay_fee = std::stoi(val_str);
                } else if (key == "permit_bare_multisig") {
                    g_permit_bare_multisig = (val_str == "true" || val_str == "1");
                } else if (key == "permit_bare_pubkey") {
                    g_permit_bare_pubkey = (val_str == "true" || val_str == "1");
                } else if (key == "reject_parasites") {
                    g_reject_parasites = (val_str == "true" || val_str == "1");
                } else if (key == "max_op_return_outputs") {
                    g_max_op_return_outputs = std::stoi(val_str);
                }
            }
        }
        file.close();
    }

    // Apply active profile (if not set to custom)
    if (g_active_profile != "custom") {
        ApplyProfileSettings(g_active_profile, mempool_opts);
    } else {
        // Apply custom values parsed from TOML file
        mempool_opts.reject_tokens = g_reject_tokens;
        mempool_opts.reject_parasites = g_reject_parasites;
        mempool_opts.permit_bare_pubkey = g_permit_bare_pubkey;
        mempool_opts.permit_bare_multisig = g_permit_bare_multisig;
        if (g_max_datacarrier_bytes > 0) {
            mempool_opts.max_datacarrier_bytes = g_max_datacarrier_bytes;
        } else {
            mempool_opts.max_datacarrier_bytes = std::nullopt;
        }
        mempool_opts.dust_relay_feerate = CFeeRate(g_dust_relay_fee);
    }

    LogPrintf("Oracle Policy: Loaded active profile: '%s' [BIP-110 Enforce: '%s', Reject Inscriptions: %d, Max OP_RETURN: %d]\n",
              g_active_profile, g_bip110_mode, g_reject_inscriptions, g_max_op_return_outputs);
}

bool SavePolicyConfig() {
    fs::path config_path = gArgs.GetDataDirNet() / "policy.toml";
    std::ofstream file(config_path);
    if (!file.is_open()) return false;

    file << "# Oracle Knots Policy Configuration\n";
    file << "# Available profiles: \"maximalist\", \"bip110-strict\", \"monetary-only\", \"default-knots\", \"custom\"\n";
    file << "profile = \"" << g_active_profile << "\"\n";
    file << "bip110_mode = \"" << g_bip110_mode << "\"  # auto (follows BIP9 consensus), always, never\n\n";

    file << "[custom_rules]\n";
    file << "datacarrier_size = " << g_max_datacarrier_bytes << "  # 0 to block OP_RETURN, 83 is standard\n";
    file << "reject_tokens = " << (g_reject_tokens ? "true" : "false") << "      # Filter Runes, BRC-20 overlay protocols\n";
    file << "reject_inscriptions = " << (g_reject_inscriptions ? "true" : "false") << " # Filter Taproot/Witness inscriptions\n";
    file << "dust_relay_fee = " << g_dust_relay_fee << "   # custom dust fee in sat/kvb\n";
    file << "permit_bare_multisig = " << (g_permit_bare_multisig ? "true" : "false") << "\n";
    file << "permit_bare_pubkey = " << (g_permit_bare_pubkey ? "true" : "false") << "\n";
    file << "reject_parasites = " << (g_reject_parasites ? "true" : "false") << "   # reject parasite locktime 21 overlays\n";
    file << "max_op_return_outputs = " << g_max_op_return_outputs << "\n";

    file.close();
    return true;
}

void IncrementRejectionCount(const std::string& reason) {
    g_rejection_counts["total"]++;
    if (g_rejection_counts.count(reason)) {
        g_rejection_counts[reason]++;
    }
}

} // namespace OraclePolicy
