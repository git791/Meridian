import json
from google.cloud import pubsub_v1
from core.config import settings

def publish_event(event_type: str, data: dict):
    """
    Publishes an event to GCP Pub/Sub. 
    Useful for triggering background tasks like post-meeting analysis.
    """
    if not settings.GCP_PROJECT or settings.DEMO_MODE:
        print(f"[PUBSUB DEMO] Event: {event_type} | Data: {data}")
        return

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(settings.GCP_PROJECT, settings.PUBSUB_TOPIC)
    
    message_data = json.dumps({
        "event_type": event_type,
        "payload": data,
        "timestamp": str(datetime.utcnow())
    }).encode("utf-8")

    try:
        future = publisher.publish(topic_path, message_data)
        return future.result()
    except Exception as e:
        print(f"Failed to publish to Pub/Sub: {e}")