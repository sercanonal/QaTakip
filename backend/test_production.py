"""
Test script for Jira and Report functionality
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

async def test_jira():
    """Test Jira connection"""
    print("\n=== JIRA CONNECTION TEST ===")
    try:
        from jira_client import jira_client
        
        # Test with SERCANO
        print("Testing Jira API for user: SERCANO")
        issues = await jira_client.get_issues_by_assignee("SERCANO", max_results=5)
        
        if issues:
            print(f"✅ SUCCESS: Found {len(issues)} issues")
            for issue in issues[:3]:
                print(f"  - {issue.get('key')}: {issue.get('fields', {}).get('summary', 'No summary')}")
        else:
            print("⚠️  No issues found or connection failed")
            
            # Try with email
            print("\nTrying with email: sercan.onal@intertech.com.tr")
            issues = await jira_client.get_issues_by_assignee("sercan.onal@intertech.com.tr", max_results=5)
            
            if issues:
                print(f"✅ SUCCESS with email: Found {len(issues)} issues")
            else:
                print("❌ Failed with both username and email")
                print("   Please check:")
                print("   1. Jira server accessible from this network")
                print("   2. API token is valid")
                print("   3. Username/email exists in Jira")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

async def test_report_generation():
    """Test report generation"""
    print("\n=== REPORT GENERATION TEST ===")
    try:
        from report_exporter import report_exporter
        
        # Sample data
        test_data = {
            'stats': {
                'total_tasks': 100,
                'completed_tasks': 75,
                'in_progress_tasks': 15,
                'todo_tasks': 10,
                'overdue_tasks': 5,
                'completion_rate': 75
            },
            'tasks': [
                {
                    'id': '1',
                    'title': 'Test Task 1',
                    'description': 'Test description',
                    'status': 'completed',
                    'priority': 'high',
                    'category_id': 'Backend',
                    'created_at': '2025-01-29T10:00:00',
                    'completed_at': '2025-01-29T15:00:00'
                },
                {
                    'id': '2',
                    'title': 'Test Task 2',
                    'description': 'Another test',
                    'status': 'in_progress',
                    'priority': 'medium',
                    'category_id': 'Frontend',
                    'created_at': '2025-01-29T11:00:00',
                    'completed_at': None
                }
            ]
        }
        
        # Test PDF
        print("Generating PDF report...")
        pdf_data = report_exporter.generate_pdf_report(test_data)
        print(f"✅ PDF generated: {len(pdf_data)} bytes")
        
        # Test Excel
        print("Generating Excel report...")
        excel_data = report_exporter.generate_excel_report(test_data)
        print(f"✅ Excel generated: {len(excel_data)} bytes")
        
        # Test Word
        print("Generating Word report...")
        word_data = report_exporter.generate_word_report(test_data)
        print(f"✅ Word generated: {len(word_data)} bytes")
        
        print("\n✅ All report formats working!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("=" * 60)
    print("QA Task Manager - Production Readiness Test")
    print("=" * 60)
    
    # Test reports first (doesn't need network)
    await test_report_generation()
    
    # Test Jira (needs network)
    await test_jira()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
