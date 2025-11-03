def calc(consumers):
    power = 0

    for pc in consumers:
        consumer = pc.consumer
        percentage = pc.percentage
        power += 100 * consumer.power * percentage

    return power
