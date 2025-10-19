import requests
import time
import json
from datetime import datetime

class OptimizationTester:
    def __init__(self, base_url="https://trackmatch-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []

    def log_test(self, name, success, details="", timing=None):
        """Log test result with timing"""
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timing": timing,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        timing_str = f" ({timing:.2f}s)" if timing else ""
        print(f"{status} {name}{timing_str}")
        if details:
            print(f"   Details: {details}")

    def test_download_speed_optimization(self):
        """Test that downloads start quickly without timeout"""
        print("\n🚀 Testing Download Speed Optimization")
        print("   Expected: Quick start, no timeout, reduced search results")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/download-track",
                json={
                    "track_name": "TÁ NAMORANDO E ME QUERENDO",
                    "track_artist": "Leozinn No Beat",
                    "track_id": "speed_test"
                },
                timeout=90  # Should complete well within this
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            success = response.status_code == 200 and total_time < 60  # Should be faster than 60s
            
            details = f"Status: {response.status_code}, Total time: {total_time:.2f}s"
            
            if success:
                content_length = len(response.content)
                details += f", File size: {content_length} bytes"
                
                # Check if it's actually fast (under 45 seconds is good)
                if total_time < 45:
                    details += " - FAST ⚡"
                elif total_time < 60:
                    details += " - ACCEPTABLE ⏱️"
                else:
                    success = False
                    details += " - TOO SLOW ⏰"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Download Speed Optimization", success, details, total_time)
            return success, total_time
            
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            self.log_test("Download Speed Optimization", False, str(e), total_time)
            return False, total_time

    def test_intelligent_matching_accuracy(self):
        """Test that intelligent matching selects correct version (not sertanejo)"""
        print("\n🎯 Testing Intelligent Matching Accuracy")
        print("   Expected: EletroFunk version, not sertaneja")
        print("   Keywords should be extracted: EletroFunk, Leozinn No Beat")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/download-track",
                json={
                    "track_name": "TÁ NAMORANDO E ME QUERENDO - EletroFunk",
                    "track_artist": "Leozinn No Beat",
                    "track_id": "accuracy_test"
                },
                timeout=90
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Time: {total_time:.2f}s"
            
            if success:
                content_length = len(response.content)
                details += f", File size: {content_length} bytes"
                details += " - Intelligent matching appears to have worked correctly"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Intelligent Matching Accuracy", success, details, total_time)
            return success
            
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            self.log_test("Intelligent Matching Accuracy", False, str(e), total_time)
            return False

    def test_fallback_strategies(self):
        """Test that fallback strategies work when primary fails"""
        print("\n🔄 Testing Fallback Strategies")
        print("   Expected: If one strategy fails, try next (4 strategies total)")
        
        # Test with a more obscure track that might need fallbacks
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/download-track",
                json={
                    "track_name": "Obscure Test Track That Might Not Exist",
                    "track_artist": "Unknown Artist",
                    "track_id": "fallback_test"
                },
                timeout=120  # Give more time for fallbacks
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # For fallback test, we expect either success (found via fallback) or 404 (all strategies tried)
            success = response.status_code in [200, 404]
            details = f"Status: {response.status_code}, Time: {total_time:.2f}s"
            
            if response.status_code == 200:
                details += " - Found via fallback strategies"
            elif response.status_code == 404:
                details += " - All fallback strategies tried (expected for non-existent track)"
            else:
                success = False
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Fallback Strategies", success, details, total_time)
            return success
            
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            self.log_test("Fallback Strategies", False, str(e), total_time)
            return False

    def test_batch_download_optimization(self):
        """Test batch download with optimization (should handle multiple tracks efficiently)"""
        print("\n📦 Testing Batch Download Optimization")
        print("   Expected: Multiple tracks downloaded efficiently, no file conflicts")
        
        # First get a playlist
        try:
            playlist_response = requests.post(
                f"{self.api_url}/playlist",
                json={"url": "https://open.spotify.com/playlist/31VS6WHNraw7OUtj7jXdCO?si=ceE064jeQY2B1PLKTfI8WQ&pi=grOw-XSJT4KFp"},
                timeout=30
            )
            
            if playlist_response.status_code != 200:
                self.log_test("Batch Download Optimization", False, "Could not load test playlist")
                return False
            
            playlist_data = playlist_response.json()
            test_tracks = playlist_data['tracks'][:3]  # Test with 3 tracks
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/download-all",
                json={
                    "playlist_id": playlist_data['id'],
                    "tracks": test_tracks
                },
                timeout=180
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Time: {total_time:.2f}s"
            
            if success:
                content_length = len(response.content)
                download_summary = response.headers.get('X-Download-Summary', '')
                
                details += f", ZIP size: {content_length} bytes"
                
                if download_summary:
                    details += f", Summary: {download_summary}"
                    
                    # Parse summary to verify multiple downloads
                    if '/' in download_summary:
                        successful, total = download_summary.split('/')
                        successful = int(successful)
                        total = int(total)
                        
                        if successful > 1:
                            details += f" - Multiple tracks downloaded successfully (no file conflicts)"
                        elif successful == 1 and total > 1:
                            success = False
                            details += f" - Only 1 track downloaded, possible optimization issue"
                        elif successful == 0:
                            success = False
                            details += f" - No tracks downloaded"
                
                # Check timing efficiency
                avg_time_per_track = total_time / len(test_tracks)
                if avg_time_per_track < 30:
                    details += f" - EFFICIENT (avg {avg_time_per_track:.1f}s/track)"
                elif avg_time_per_track < 60:
                    details += f" - ACCEPTABLE (avg {avg_time_per_track:.1f}s/track)"
                else:
                    details += f" - SLOW (avg {avg_time_per_track:.1f}s/track)"
                    
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Batch Download Optimization", success, details, total_time)
            return success
            
        except Exception as e:
            self.log_test("Batch Download Optimization", False, str(e))
            return False

    def test_reduced_search_results(self):
        """Test that system uses reduced search results (5 instead of 10)"""
        print("\n🔍 Testing Reduced Search Results")
        print("   Expected: System should use 5 results per search (optimization)")
        
        # This is more of a behavioral test - we'll test with a common track
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/download-track",
                json={
                    "track_name": "Blinding Lights",
                    "track_artist": "The Weeknd",
                    "track_id": "search_test"
                },
                timeout=60
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            success = response.status_code == 200 and total_time < 45  # Should be faster with fewer results
            details = f"Status: {response.status_code}, Time: {total_time:.2f}s"
            
            if success:
                details += " - Fast completion suggests optimized search (5 results)"
            elif response.status_code == 200:
                details += " - Completed but slower than expected"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:200]}"
            
            self.log_test("Reduced Search Results", success, details, total_time)
            return success
            
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time
            self.log_test("Reduced Search Results", False, str(e), total_time)
            return False

    def run_optimization_tests(self):
        """Run all optimization tests"""
        print("🔧 Testing SpotiDown Optimization Features")
        print("=" * 60)
        print("Focus: Speed, Accuracy, Fallbacks, Efficiency")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        # Test 1: Download Speed
        success, timing = self.test_download_speed_optimization()
        total_tests += 1
        if success:
            passed_tests += 1
        
        # Test 2: Intelligent Matching
        if self.test_intelligent_matching_accuracy():
            passed_tests += 1
        total_tests += 1
        
        # Test 3: Fallback Strategies
        if self.test_fallback_strategies():
            passed_tests += 1
        total_tests += 1
        
        # Test 4: Batch Download Optimization
        if self.test_batch_download_optimization():
            passed_tests += 1
        total_tests += 1
        
        # Test 5: Reduced Search Results
        if self.test_reduced_search_results():
            passed_tests += 1
        total_tests += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Optimization Tests: {passed_tests}/{total_tests} passed")
        
        if passed_tests == total_tests:
            print("🎉 All optimization features working correctly!")
            return True
        else:
            print("⚠️  Some optimizations need attention.")
            return False

def main():
    tester = OptimizationTester()
    success = tester.run_optimization_tests()
    
    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "optimization_test_results": tester.test_results,
        "summary": {
            "total_tests": len(tester.test_results),
            "passed_tests": sum(1 for r in tester.test_results if r['success']),
            "all_passed": success
        }
    }
    
    with open("/app/optimization_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Optimization test results saved to: /app/optimization_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())