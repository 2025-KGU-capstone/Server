import face_recognition
import os

def load_visitor_encodings():
    visitor_encodings = {}

    for filename in os.listdir("visitor"):
        if not filename.endswith(".jpg"):
            continue

        visitor_path = os.path.join("visitor", filename)
        print(f"[INIT] Loading and encoding: {filename}")

        known_image = face_recognition.load_image_file(visitor_path)
        known_locations = face_recognition.face_locations(known_image)
        if not known_locations:
            print(f"[INIT] No faces detected in {filename}, skipping.")
            continue

        known_encodings = face_recognition.face_encodings(known_image, known_locations)
        if not known_encodings:
            print(f"[INIT] Failed to extract encoding from {filename}, skipping.")
            continue

        visitor_encodings[filename.replace(".jpg", "")] = known_encodings[0]

    print(f"[INIT] Loaded {len(visitor_encodings)} visitor encodings.")
    return visitor_encodings


def recognize_person_from_image(image, visitor_encodings):
    print("[DEBUG] Starting face recognition", flush=True)

    try:
        face_locations = face_recognition.face_locations(image)
        print("[DEBUG] face_locations() call succeeded", flush=True)
    except Exception as e:
        print(f"[ERROR] face_locations() failed: {e}", flush=True)
        return None

    if not face_locations:
        print("[DEBUG] No faces detected in captured image.", flush=True)
        return None

    print(f"[DEBUG] Detected {len(face_locations)} face(s) in captured image.", flush=True)

    try:
        face_encodings = face_recognition.face_encodings(image, face_locations)
        print("[DEBUG] face_encodings() call succeeded", flush=True)
    except Exception as e:
        print(f"[ERROR] face_encodings() failed: {e}", flush=True)
        return None

    if not face_encodings:
        print("[DEBUG] Failed to extract encodings from captured image.", flush=True)
        return None

    for idx, face_encoding in enumerate(face_encodings):
        print(f"[DEBUG] Processing face {idx + 1}", flush=True)

        for name, known_encoding in visitor_encodings.items():
            match = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
            print(f"[DEBUG] Comparing with {name} → Match result: {match}", flush=True)

            if True in match:
                print(f"[DEBUG] ✅ Match found: {name}", flush=True)
                return name

    print("[DEBUG] ❌ No match found for any registered images.", flush=True)
    return None


