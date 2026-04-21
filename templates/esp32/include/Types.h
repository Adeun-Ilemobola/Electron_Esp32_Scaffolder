enum class KindMode {
  REGISTER,
  STATE,
  COMMAND,
  RESPONSE
};
inline const char* kindModeToString(KindMode kind) {
    switch (kind) {
        case KindMode::REGISTER: return "register";
        case KindMode::STATE:    return "state";
        case KindMode::COMMAND:  return "command";
        case KindMode::RESPONSE: return "response";
        default:                 return "unknown";
    }
}