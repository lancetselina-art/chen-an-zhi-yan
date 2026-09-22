from core.reporting import vision_to_markdown, sensor_to_markdown
def vision(data, context): return vision_to_markdown(data, context)
def sensor(data, features, context): return sensor_to_markdown(data, features, context)
