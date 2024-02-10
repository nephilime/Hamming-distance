import av
import json
import os
import imagehash
import PIL.Image as Image

input_file_ref = "output_video.ts" #output_video.ts
input_file = "output_video_000102_05.ts"

def xor_hashes(hash1, hash2):
    return int(hash1, 16) ^ int(hash2, 16)

def frames_to_TC (frames):
    h = int(frames / 86400) 
    m = int(frames / 1440) % 60 
    s = int((frames % 1440)/24) 
    f = frames % 1440 % 24
    return ( "%02d:%02d:%02d:%02d" % ( h, m, s, f))

def get_frames(input_file,save_frames=False): 
    if not os.path.exists("./" + input_file.replace(".ts", "")):
        os.makedirs("./" + input_file.replace(".ts", ""))

    container = av.open(input_file, options={'backward':"True",'any_frame': "True"})      
    stream = container.streams.video[0]    
    hash_file = {}
    # stream.codec_context.skip_frame = "NONKEY"
    try:
        for frame in container.decode(stream):
            print(frame)
            gray_frame = frame.reformat(format='gray16') #gray16
            # bytes = gray_frame.to_ndarray().shape
            image = Image.fromarray(frame.to_ndarray(), mode='L')

            # bytes = gray_frame.to_image().tobytes()
            # readable_hash = hashlib.sha256(bytes).hexdigest();
            
            readable_hash = imagehash.phash(image, hash_size=32)
            hash_as_str = str(readable_hash)
            # average_hash(image).hash
            
            # print(readable_hash)
            hash_file[frame.index] = hash_as_str
            if save_frames:
                gray_frame.to_image().save(
                    "./" + "./" + input_file.replace(".ts", "") + "/ref.{:04d}_{:04d}.jpg".format(frame.pts, frame.index),
                    quality=80,
                )
    except Exception as e:
        if isinstance(e, av.AVError):
            print(e)
        else:
            raise e
    finally:
        with open(input_file.replace(".ts", ".json"), "w") as file:
            # hash_file_serializable = {k: v.tolist() for k, v in hash_file.items()}  # Convert ndarray to list
            json.dump(hash_file, file)  # Serialize the dictionary to JSON
            # print(hash_file)
        container.close()
    return True

hash_file_content = get_frames(input_file)     
# hash_file_content = get_frames(input_file_ref)     

ref_json = json.load(open(input_file_ref.replace(".ts", ".json")))
json_content = json.load(open(input_file.replace(".ts", ".json")))

def xor_hashes(hash1, hash2):
    n_hash1 = imagehash.hex_to_hash(hash1)
    n_hash2 = imagehash.hex_to_hash(hash2)

    imh1 = imagehash.ImageHash(n_hash1).hash
    imh2 = imagehash.ImageHash(n_hash2).hash

    rest = imh1 - imh2
    
    return rest

def compare_hashes(ref_json, json_content):
    diff = {}
    for key in ref_json:        
        diff[key] = xor_hashes(json_content["0"], ref_json[key])
        if diff[key] == 0 :
            print("No difference:" + str(key))
    min_diff_key = min(diff, key=diff.get) 
    return frames_to_TC(int(min_diff_key)) + " Hamming distance: " + str(diff[min_diff_key]) 
         
print(compare_hashes(ref_json, json_content))

#TODO:
# 1. Add a way to compare the hashes and find the closest frame
# 2. Add compare all frame in cuted wideo
# 3. encoder should transfer hash of freames to client in separate stream to compare them on client side...

#ffmpeg -ss 00:00:21 -i ./output_video.ts -t 5 -c libx264 -preset ultrafast -profile:v baseline -level 3.1 -b:v 2000k -pix_fmt yuv420p -g 48 -bf 0  -f mpegts ./output_video_00002100_05.ts
#"504": "153af53a6636482652b0bbfb31e8b4e7b1b880346f82cb733b30164a54edff8f"
#  "0": "be1f139406fef20249e6b7e0b91645580ba0601ca401710c7e8909a9fa1dd17f"
