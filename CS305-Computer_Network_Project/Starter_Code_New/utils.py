import hashlib
import uuid

def generate_message_id(data=None):
    if data:
        return hashlib.sha256(data.encode()).hexdigest()
    else:
        return str(uuid.uuid4())