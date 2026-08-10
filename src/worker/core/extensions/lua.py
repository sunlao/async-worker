def claim_script():
    return """
    local current = redis.call("GET", KEYS[1])
    if not current then
        redis.call("SET", KEYS[1], ARGV[1])
        return 1
    end
    if current == ARGV[1] then
        return 1
    end
    return 0"""


def release_script():
    return """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    end
    return 0"""
