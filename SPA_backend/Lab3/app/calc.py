def calc(reserve):
    power = 0

    consumers = reserve["consumers"]
    for consumer in consumers:
        power += consumer['power'] * consumer['percentage'] * (-1 * reserve["temperature"]) * 0.05

    return power