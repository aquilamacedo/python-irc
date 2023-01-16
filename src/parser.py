def parse_message(message):
    start_idx = 0
    prefix = None

    if message[start_idx] == ':':
        end_idx = message.index(' ', start_idx)

        prefix = message[start_idx + 1:end_idx]
        start_idx = end_idx + 1

    if ' ' in message[start_idx:]:
        end_idx = message.index(' ', start_idx)
    else:
        end_idx = len(message)

    command = message[start_idx:end_idx]
    start_idx = end_idx + 1
    trailing = None

    if ':' in message[start_idx:]:
        end_idx = message.index(':', start_idx)
        middle = list(filter(None, message[start_idx:end_idx].split(' ')))
        start_idx = end_idx + 1
        trailing = message[start_idx:]
    else:
        middle = list(filter(None, message[start_idx:].split(' ')))

    return prefix, command, middle, trailing
