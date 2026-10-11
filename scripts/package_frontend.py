import os
import zipfile
import stat

def package(output_zip=None):
    dist_dir = os.path.abspath("frontend/dist")
    zip_path = os.path.abspath(output_zip or os.environ.get("AMPLIFY_ZIP_PATH", "frontend/amplify-dist-preflight.zip"))
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    print(f"Packaging {dist_dir} into {zip_path} with standard POSIX headers...")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(dist_dir):
            for d in dirs:
                dir_full = os.path.join(root, d)
                rel_dir = os.path.relpath(dir_full, dist_dir).replace("\\", "/") + "/"
                zinfo = zipfile.ZipInfo(rel_dir)
                zinfo.create_system = 3  # Unix
                # drwxr-xr-x
                zinfo.external_attr = (stat.S_IFDIR | 0o755) << 16
                z.writestr(zinfo, "")
                print(f"  Added directory: {rel_dir}")
                
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir).replace("\\", "/")
                with open(full_path, "rb") as f:
                    data = f.read()
                zinfo = zipfile.ZipInfo(rel_path)
                zinfo.create_system = 3  # Unix
                # -rw-r--r--
                zinfo.external_attr = (stat.S_IFREG | 0o644) << 16
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zinfo, data)
                print(f"  Added file: {rel_path} ({len(data)} bytes)")
                
    print(f"Successfully created {zip_path} ({os.path.getsize(zip_path)} bytes).")

if __name__ == "__main__":
    package()
