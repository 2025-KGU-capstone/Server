# app/routes/__init__.py

from .webcam_router import (
    webcam_bp,
    capture_picture,
    start,
    stop,
    video_feed_route,
)

from .visitor_router import (
    visitor_bp,
	upload,
	get_images,
	get_image,
	delete,
)

# from .ngrok_router import (
#     ngrok_bp,
#     start_ngrok,
#     ngrok_status,
# )

from .notifications_router import (
	notifications_bp,
	send_notification,
)

__all__ = [
    "webcam_bp", "capture_picture", "start", "stop", "video_feed_route",
    "visitor_bp", "upload", "get_images", "get_image", "delete",
    #"ngrok_bp", "start_ngrok", "ngrok_status",
    "notifications_bp", "send_notification",
]
