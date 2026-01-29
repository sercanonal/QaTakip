#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  1. Login sayfasında "Adınız" yerine "Intertech Kullanıcı Adı" field'ı, placeholder "SERCANO"
  2. Admin API endpoint'leri - kullanıcı listesini yönetme (ekleme, silme, güncelleme)
  3. Gerçek zamanlı bildirim sistemi - SSE ile sayfa refresh'e gerek kalmadan bildirim gelsin

backend:
  - task: "Admin API - Kullanıcı Yönetimi"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "GET /api/admin/users, POST /api/admin/users, PUT /api/admin/users/{id}, DELETE /api/admin/users/{id} endpoint'leri eklendi"
      - working: true
        agent: "testing"
        comment: "✅ Tüm Admin API endpoint'leri test edildi ve başarılı: GET /api/admin/users (42 kullanıcı listelendi), POST /api/admin/users (yeni kullanıcı oluşturuldu), PUT /api/admin/users/{id} (kullanıcı adı güncellendi), DELETE /api/admin/users/{id} (kullanıcı ve verileri silindi). Data integrity kontrolü geçti."
  
  - task: "SSE Bildirim Sistemi"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "NotificationManager class ve GET /api/notifications/stream SSE endpoint'i eklendi. Görev atandığında gerçek zamanlı bildirim push edilir."
      - working: true
        agent: "testing"
        comment: "✅ SSE bildirim sistemi tam çalışır durumda: GET /api/notifications/stream endpoint'i erişilebilir, doğru content-type (text/event-stream) döndürüyor, bağlantı mesajı alınıyor. Görev atandığında bildirimler oluşturuluyor ve GET /api/notifications ile alınabiliyor. Bildirim okuma/silme işlemleri çalışıyor."

frontend:
  - task: "Login Sayfası Güncelleme"
    implemented: true
    working: "NA"
    file: "pages/Login.jsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Label 'Intertech Kullanıcı Adı', placeholder 'SERCANO' olarak güncellendi"
  
  - task: "SSE Client Bağlantısı"
    implemented: true
    working: "NA"
    file: "components/Layout.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "EventSource ile SSE bağlantısı kuruldu. Yeni bildirimler otomatik olarak UI'a eklenir."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Admin API - Kullanıcı Yönetimi"
    - "SSE Bildirim Sistemi"
    - "SSE Client Bağlantısı"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Üç ana özellik eklendi:
      1. Login sayfası güncellendi
      2. Admin API endpoint'leri eklendi (kullanıcı CRUD)
      3. SSE ile gerçek zamanlı bildirim sistemi
      
      Backend test edilmeli:
      - Admin endpoint'leri (GET, POST, PUT, DELETE /api/admin/users)
      - SSE stream endpoint'i (/api/notifications/stream)
      - Görev atandığında bildirim gönderimi
      
      Frontend'de SSE bağlantısını test etmek için:
      - Bir kullanıcı login olsun
      - Başka bir kullanıcı ona görev atasın
      - Bildirim anında gelmeli (sayfa refresh'e gerek yok)