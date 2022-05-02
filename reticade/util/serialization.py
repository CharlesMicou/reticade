import pickle
import base64

"""
Note: this is a quick-and-dirty way of storing arbitrary objects in the json
serialisation. It's not robust and we should prefer reconstructing from
constructor parameters, but is useful for saving opaque classes like scikit
learn models.
It can be temporarily (grossly) misused to store things like reference image data.
"""
def obj_to_picklestring(obj_to_save):
    raw = pickle.dumps(obj_to_save)
    # Omit the b'' indicators in string representation
    as_string = str(base64.b64encode(raw))[2:-1]
    return as_string

def obj_from_picklestring(obj_to_extract):
    as_bytes = base64.b64decode(obj_to_extract.encode('utf-8'))
    return pickle.loads(as_bytes)