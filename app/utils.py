import base64

def encode_this_string(string):
    byte_string = string.encode("utf-8")
    byte_encoded = base64.b64encode(byte_string)
    return byte_encoded.decode("utf-8")

def decode_this_string(sting):
    byte_string = sting.encode('utf-8')
    byte_decoded = base64.b64decode(identificator_bytes)
    return byte_decoded.decode('utf-8')
