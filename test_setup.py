"""
Quick Test Script - Verify AI Report Generator Setup
Run this to check if everything is working
"""

import sys
import subprocess

def check_ollama():
    """Check if Ollama is accessible"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
        if 'llama3.2' in result.stdout:
            print("✅ Ollama is running with Llama 3.2 model")
            return True
        else:
            print("⚠️  Ollama is running but Llama 3.2 not found")
            print("   Run: ollama pull llama3.2")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Install from: https://ollama.ai")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_dependencies():
    """Check if Python packages are installed"""
    required = ['flask', 'langchain', 'langchain_community']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages with:")
        print(f"pip install -r requirements.txt")
        return False
    return True

def test_report_generation():
    """Test basic report generation"""
    try:
        from report_generator import ReportGenerator
        
        print("\n🧪 Testing report generation...")
        generator = ReportGenerator()
        
        test_data = """product,sales,profit
Laptop,15000,3000
Phone,25000,5000"""
        
        report = generator.generate_report(test_data, 'csv')
        
        if len(report) > 100 and "BUSINESS INTELLIGENCE REPORT" in report:
            print("✅ Report generation working!")
            return True
        else:
            print("⚠️  Report generated but seems incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def main():
    print("="*60)
    print("AI REPORT GENERATOR - SYSTEM CHECK")
    print("="*60)
    print()
    
    checks = [
        ("Ollama Setup", check_ollama),
        ("Python Dependencies", check_dependencies),
        ("Report Generation", test_report_generation)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking: {name}")
        print("-" * 60)
        results.append(check_func())
    
    print("\n" + "="*60)
    if all(results):
        print("🎉 ALL CHECKS PASSED! You're ready to go!")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Upload data and generate reports!")
    else:
        print("⚠️  Some checks failed. Fix the issues above and try again.")
    print("="*60)

if __name__ == "__main__":
    main()
