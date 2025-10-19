#!/usr/bin/env python3

import requests
import sys
import json
import zipfile
import io
from datetime import datetime

def test_batch_download():
    """Test the batch download fix specifically"""
    base_url = "https://spotify-downloader-5.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 Testing SpotiDown Batch Download Fix")
    print(f"🔗 API URL: {api_url}")
    print("=" * 60)
    
    # Step 1: Load the specific playlist
    playlist_url = "https://open.spotify.com/playlist/31VS6WHNraw7OUtj7jXdCO?si=ceE064jeQY2B1PLKTfI8WQ&pi=grOw-XSJT4KFp"
    
    print("📋 Step 1: Loading playlist...")
    try:
        response = requests.post(
            f"{api_url}/playlist",
            json={"url": playlist_url},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to load playlist: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
        
        playlist_data = response.json()
        print(f"✅ Playlist loaded: {playlist_data['name']}")
        print(f"   Total tracks: {playlist_data['total_tracks']}")
        
        # Use first 3-4 tracks as requested
        tracks_to_test = playlist_data['tracks'][:4] if len(playlist_data['tracks']) >= 4 else playlist_data['tracks'][:3]
        
        print(f"\n🎵 Selected {len(tracks_to_test)} tracks for testing:")
        for i, track in enumerate(tracks_to_test):
            print(f"   {i+1}. {track['name']} - {track['artist']}")
        
    except Exception as e:
        print(f"❌ Exception loading playlist: {e}")
        return False
    
    # Step 2: Test batch download
    print(f"\n📦 Step 2: Testing batch download...")
    try:
        response = requests.post(
            f"{api_url}/download-all",
            json={
                "playlist_id": playlist_data['id'],
                "tracks": tracks_to_test
            },
            timeout=300  # 5 minutes timeout for batch downloads
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Batch download failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return False
        
        # Check response headers
        content_type = response.headers.get('content-type', '')
        content_length = len(response.content)
        download_summary = response.headers.get('X-Download-Summary', '')
        failed_tracks = response.headers.get('X-Failed-Tracks', '')
        
        print(f"✅ Batch download completed")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Length: {content_length} bytes")
        print(f"   Download Summary: {download_summary}")
        if failed_tracks:
            print(f"   Failed Tracks: {failed_tracks}")
        
        # Verify it's a ZIP file
        if 'zip' not in content_type and 'application/octet-stream' not in content_type:
            print(f"❌ Unexpected content type: {content_type}")
            return False
        
        if content_length == 0:
            print(f"❌ Empty ZIP file")
            return False
        
        # Step 3: Analyze ZIP contents
        print(f"\n🔍 Step 3: Analyzing ZIP contents...")
        try:
            zip_data = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_data, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"   Files in ZIP: {len(file_list)}")
                
                for i, filename in enumerate(file_list):
                    file_info = zip_file.getinfo(filename)
                    print(f"   {i+1}. {filename} ({file_info.file_size} bytes)")
                
                # Check if filenames are clean (no technical prefixes)
                clean_names = True
                for filename in file_list:
                    if filename.startswith('track_') and '_' in filename:
                        # Check if it still has technical prefixes
                        parts = filename.split('_')
                        if len(parts) >= 3 and parts[0] == 'track' and parts[1].isdigit():
                            clean_names = False
                            print(f"   ⚠️  File still has technical prefix: {filename}")
                
                if clean_names:
                    print(f"   ✅ All filenames are clean (no technical prefixes)")
                else:
                    print(f"   ❌ Some files still have technical prefixes")
        
        except zipfile.BadZipFile:
            print(f"❌ Invalid ZIP file")
            return False
        except Exception as e:
            print(f"❌ Error analyzing ZIP: {e}")
            return False
        
        # Step 4: Verify the fix worked
        print(f"\n🎯 Step 4: Verifying the batch download fix...")
        
        # Parse download summary
        if download_summary and '/' in download_summary:
            successful, total = download_summary.split('/')
            successful = int(successful)
            total = int(total)
            
            print(f"   Downloaded: {successful}/{total} tracks")
            
            if successful == 0:
                print(f"❌ No tracks were downloaded")
                return False
            elif successful == 1 and total > 1:
                print(f"❌ Only 1 track downloaded out of {total} - possible file overwrite issue")
                return False
            elif successful > 1:
                print(f"✅ Multiple tracks downloaded successfully - fix appears to be working")
                
                # Verify ZIP contains the expected number of files
                if len(file_list) == successful:
                    print(f"✅ ZIP contains expected number of files ({successful})")
                else:
                    print(f"⚠️  ZIP contains {len(file_list)} files but {successful} were reported as successful")
                
                return True
            else:
                print(f"✅ {successful} tracks downloaded successfully")
                return True
        else:
            print(f"❌ Missing or invalid download summary header")
            return False
            
    except Exception as e:
        print(f"❌ Exception during batch download: {e}")
        return False

def main():
    success = test_batch_download()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Batch download fix test PASSED!")
        print("✅ The file overwrite issue appears to be resolved")
    else:
        print("❌ Batch download fix test FAILED!")
        print("⚠️  The file overwrite issue may still exist")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())