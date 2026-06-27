#ifndef BITCOIN_POLICY_ORACLE_POLICY_H
#define BITCOIN_POLICY_ORACLE_POLICY_H

#include <kernel/mempool_options.h>
#include <primitives/transaction.h>
#include <string>
#include <map>

namespace OraclePolicy {

// The active policy profile: maximalist, bip110-strict, monetary-only, default-knots, custom
extern std::string g_active_profile;

// BIP-110 Enforcement Mode: auto, always, never
extern std::string g_bip110_mode;

// Configurable parameters
extern int g_max_datacarrier_bytes;
extern bool g_reject_tokens;
extern bool g_reject_inscriptions;
extern int g_dust_relay_fee;
extern bool g_permit_bare_multisig;
extern bool g_permit_bare_pubkey;
extern bool g_reject_parasites;
extern int g_max_op_return_outputs;

// Uptime tracking for observability
extern int64_t g_startup_time;

// Rejection counters
extern std::map<std::string, uint64_t> g_rejection_counts;

// Helper to check if a transaction contains an inscription envelope
bool HasInscription(const CTransaction& tx);

// Check if a transaction has too many OP_RETURN outputs
bool ExceedsMaxOpReturns(const CTransaction& tx);

// Load the policy configuration from policy.toml (creates a default one if missing)
void LoadPolicyConfig(kernel::MemPoolOptions& mempool_opts);

// Save the active policy configuration to policy.toml
bool SavePolicyConfig();

// Apply a profile's settings to MemPoolOptions
void ApplyProfileSettings(const std::string& profile_name, kernel::MemPoolOptions& mempool_opts);

// Increment rejection counter
void IncrementRejectionCount(const std::string& reason);

} // namespace OraclePolicy

#endif // BITCOIN_POLICY_ORACLE_POLICY_H
