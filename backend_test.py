import requests
import sys
import json
from datetime import datetime

class SpotifyPlaylistDownloaderTester:
    def __init__(self, base_url="https://musicport.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, str(e))
            return False

    def test_playlist_endpoint_valid(self):
        """Test playlist endpoint with valid Spotify URL"""
        # Using a known public Spotify playlist
        test_url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"  # Today's Top Hits
        
        try:
            response = requests.post(
                f"{self.api_url}/playlist",
                json={"url": test_url},
                timeout=30
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                # Validate response structure
                required_fields = ['id', 'name', 'total_tracks', 'tracks']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    details += f", Playlist: {data['name']}, Tracks: {data['total_tracks']}"
                    
                    # Validate track structure
                    if data['tracks'] and len(data['tracks']) > 0:
                        track = data['tracks'][0]
                        track_fields = ['id', 'name', 'artist', 'album', 'duration_ms']
                        missing_track_fields = [field for field in track_fields if field not in track]
                        if missing_track_fields:
                            success = False
                            details += f", Missing track fields: {missing_track_fields}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Playlist Endpoint (Valid URL)", success, details)
            return success, response.json() if success else None
            
        except Exception as e:
            self.log_test("Playlist Endpoint (Valid URL)", False, str(e))
            return False, None

    def test_playlist_endpoint_invalid(self):
        """Test playlist endpoint with invalid URL"""
        test_url = "https://invalid-url.com/not-a-playlist"
        
        try:
            response = requests.post(
                f"{self.api_url}/playlist",
                json={"url": test_url},
                timeout=10
            )
            
            # Should return 400 for invalid URL
            success = response.status_code == 400
            details = f"Status: {response.status_code}"
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    details += f", Error message: {error_data.get('detail', 'No detail')}"
                except:
                    details += ", No JSON response"
            
            self.log_test("Playlist Endpoint (Invalid URL)", success, details)
            return success
            
        except Exception as e:
            self.log_test("Playlist Endpoint (Invalid URL)", False, str(e))
            return False

    def test_download_track_endpoint(self):
        """Test individual track download endpoint"""
        # First get a playlist to have track data
        playlist_success, playlist_data = self.test_playlist_endpoint_valid()
        
        if not playlist_success or not playlist_data or not playlist_data.get('tracks'):
            self.log_test("Download Track Endpoint", False, "No playlist data available for testing")
            return False
        
        # Use first track for testing
        track = playlist_data['tracks'][0]
        
        try:
            response = requests.post(
                f"{self.api_url}/download-track",
                json={
                    "track_name": track['name'],
                    "track_artist": track['artist'],
                    "track_id": track['id']
                },
                timeout=60  # Downloads can take time
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                # Check if response is a file (binary data)
                content_type = response.headers.get('content-type', '')
                if 'audio' in content_type or 'application/octet-stream' in content_type:
                    details += f", Content-Type: {content_type}, Size: {len(response.content)} bytes"
                else:
                    success = False
                    details += f", Unexpected content-type: {content_type}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Download Track Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Download Track Endpoint", False, str(e))
            return False

    def test_download_all_endpoint(self):
        """Test download all tracks endpoint"""
        # First get a playlist to have track data
        playlist_success, playlist_data = self.test_playlist_endpoint_valid()
        
        if not playlist_success or not playlist_data:
            self.log_test("Download All Endpoint", False, "No playlist data available for testing")
            return False
        
        # Limit to first 2 tracks for testing to avoid long download times
        limited_tracks = playlist_data['tracks'][:2] if playlist_data.get('tracks') else []
        
        if not limited_tracks:
            self.log_test("Download All Endpoint", False, "No tracks available for testing")
            return False
        
        try:
            response = requests.post(
                f"{self.api_url}/download-all",
                json={
                    "playlist_id": playlist_data['id'],
                    "tracks": limited_tracks
                },
                timeout=120  # Batch downloads can take longer
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                # Check if response is a ZIP file
                content_type = response.headers.get('content-type', '')
                if 'zip' in content_type or 'application/octet-stream' in content_type:
                    details += f", Content-Type: {content_type}, Size: {len(response.content)} bytes"
                else:
                    success = False
                    details += f", Unexpected content-type: {content_type}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Download All Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Download All Endpoint", False, str(e))
            return False

    def test_cors_headers(self):
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.api_url}/", timeout=10)
            success = response.status_code in [200, 204]
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            details = f"Status: {response.status_code}, CORS Headers: {cors_headers}"
            self.log_test("CORS Headers", success, details)
            return success
            
        except Exception as e:
            self.log_test("CORS Headers", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Spotify Playlist Downloader Backend Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Test API availability first
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False
        
        # Test all endpoints
        self.test_cors_headers()
        self.test_playlist_endpoint_valid()
        self.test_playlist_endpoint_invalid()
        
        # Note: Download tests are commented out as they require actual downloads
        # which can be slow and may fail due to external dependencies
        print("\n⚠️  Skipping download tests (require external services and can be slow)")
        # self.test_download_track_endpoint()
        # self.test_download_all_endpoint()
        
        print("\n" + "=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

def main():
    tester = SpotifyPlaylistDownloaderTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": f"{(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%",
        "test_details": tester.test_results
    }
    
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())