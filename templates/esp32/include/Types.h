#pragma once
enum class KindMode {
  REGISTER,
  STATE,
  COMMAND,
  RESPONSE,
  LOG
};
inline const char* kindModeToString(KindMode kind) {
    switch (kind) {
        case KindMode::REGISTER: return "register";
        case KindMode::STATE:    return "state";
        case KindMode::COMMAND:  return "command";
        case KindMode::RESPONSE: return "response";
        case KindMode::LOG: return "log";
        default:                 return "unknown";
    }
}