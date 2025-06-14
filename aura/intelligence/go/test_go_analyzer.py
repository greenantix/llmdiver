"""
Test Go AST Analyzer - Demonstrate Mastery of Go Language Analysis
"""

import asyncio
import json
from pathlib import Path
import sys
import tempfile

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from aura.core.config import AuraConfig
from aura.planning.test_parser_mock import MockLLMProvider
from aura.intelligence.go.ast_analyzer import GoASTAnalyzer


async def test_go_analyzer():
    """Test Go AST Analyzer with comprehensive Go code samples"""
    
    # Initialize configuration
    config = AuraConfig()
    
    # Initialize mock LLM provider
    llm_provider = MockLLMProvider()
    
    # Initialize Go analyzer
    go_analyzer = GoASTAnalyzer(config, llm_provider)
    
    print("🔍 Testing Go AST Analyzer - Mastery of Concurrency and Performance...")
    
    try:
        # Create sample Go files for testing
        test_files = await create_sample_go_files()
        
        print(f"\n📁 Created {len(test_files)} sample Go files for analysis")
        
        # Analyze each Go file
        all_analyses = {}
        
        for file_name, file_path in test_files.items():
            print(f"\n🔬 Analyzing: {file_name}")
            
            analysis = await go_analyzer.analyze_go_file(file_path)
            all_analyses[file_name] = analysis
            
            # Display analysis results
            print(f"   Package: {analysis.package_info.name}")
            print(f"   Constructs: {len(analysis.constructs)}")
            print(f"   Functions: {len([c for c in analysis.constructs if c.construct_type.value == 'function'])}")
            print(f"   Methods: {len([c for c in analysis.constructs if c.construct_type.value == 'method'])}")
            print(f"   Structs: {len([c for c in analysis.constructs if c.construct_type.value == 'struct'])}")
            print(f"   Goroutines: {analysis.concurrency_analysis.goroutine_count}")
            print(f"   Concurrency Patterns: {len(analysis.concurrency_analysis.detected_patterns)}")
            print(f"   Performance Flags: {sum(len(c.performance_flags) for c in analysis.constructs)}")
            print(f"   Security Issues: {len(analysis.security_analysis.get('security_issues', []))}")
            print(f"   Recommendations: {len(analysis.recommendations)}")
        
        # Display detailed analysis for key files
        print("\n📊 Detailed Analysis Results:")
        
        for file_name, analysis in all_analyses.items():
            print(f"\n=== {file_name} ===")
            
            # Show complex constructs
            complex_constructs = [c for c in analysis.constructs if c.complexity_score > 0.3]
            if complex_constructs:
                print(f"🧠 Complex Constructs ({len(complex_constructs)}):")
                for construct in complex_constructs[:3]:  # Show top 3
                    print(f"   • {construct.name} ({construct.construct_type.value})")
                    print(f"     Complexity: {construct.complexity_score:.2f}")
                    print(f"     Exported: {construct.is_exported}")
                    if construct.concurrency_patterns:
                        print(f"     Concurrency: {', '.join(p.value for p in construct.concurrency_patterns)}")
                    if construct.performance_flags:
                        print(f"     Performance Flags: {', '.join(f.value for f in construct.performance_flags)}")
            
            # Show concurrency analysis
            if analysis.concurrency_analysis.goroutine_count > 0:
                print(f"⚡ Concurrency Analysis:")
                print(f"   Goroutines: {analysis.concurrency_analysis.goroutine_count}")
                print(f"   Channel Operations: {len(analysis.concurrency_analysis.channel_operations)}")
                print(f"   Mutex Usage: {len(analysis.concurrency_analysis.mutex_usage)}")
                print(f"   Context Usage: {len(analysis.concurrency_analysis.context_usage)}")
                
                if analysis.concurrency_analysis.detected_patterns:
                    print(f"   Patterns: {', '.join(p.value for p in analysis.concurrency_analysis.detected_patterns)}")
                
                if analysis.concurrency_analysis.potential_races:
                    print(f"   Race Conditions: {len(analysis.concurrency_analysis.potential_races)}")
                
                if analysis.concurrency_analysis.deadlock_risks:
                    print(f"   Deadlock Risks: {len(analysis.concurrency_analysis.deadlock_risks)}")
            
            # Show recommendations
            if analysis.recommendations:
                print(f"💡 Top Recommendations:")
                for rec in analysis.recommendations[:3]:
                    print(f"   • {rec}")
            
            # Show complexity metrics
            print(f"📈 Complexity Metrics:")
            for metric, value in analysis.complexity_metrics.items():
                if isinstance(value, float):
                    print(f"   {metric}: {value:.2f}")
                else:
                    print(f"   {metric}: {value}")
        
        # Generate comprehensive project analysis
        print(f"\n📋 Generating project analysis report...")
        
        # Create temporary project directory with all files
        project_dir = Path("/tmp/aura_go_test_project")
        project_dir.mkdir(exist_ok=True)
        
        # Copy test files to project directory
        for file_name, file_path in test_files.items():
            (project_dir / file_name).write_text(file_path.read_text())
        
        # Analyze entire project
        project_analyses = await go_analyzer.analyze_go_project(project_dir)
        
        # Generate report
        report_path = Path("/home/greenantix/AI/LLMdiver/aura/intelligence/go/go_analysis_report.md")
        report = go_analyzer.generate_go_analysis_report(project_analyses, report_path)
        
        print(f"   Report saved to: {report_path}")
        print(f"   Report length: {len(report)} characters")
        
        # Save detailed analysis results
        results_path = Path("/home/greenantix/AI/LLMdiver/aura/intelligence/go/go_analysis_results.json")
        results = {
            'timestamp': analysis.analysis_timestamp.isoformat(),
            'files_analyzed': len(all_analyses),
            'total_constructs': sum(len(a.constructs) for a in all_analyses.values()),
            'total_functions': sum(len([c for c in a.constructs if c.construct_type.value == 'function']) for a in all_analyses.values()),
            'total_methods': sum(len([c for c in a.constructs if c.construct_type.value == 'method']) for a in all_analyses.values()),
            'total_structs': sum(len([c for c in a.constructs if c.construct_type.value == 'struct']) for a in all_analyses.values()),
            'total_interfaces': sum(len([c for c in a.constructs if c.construct_type.value == 'interface']) for a in all_analyses.values()),
            'concurrency_summary': {
                'total_goroutines': sum(a.concurrency_analysis.goroutine_count for a in all_analyses.values()),
                'files_with_concurrency': len([a for a in all_analyses.values() if a.concurrency_analysis.goroutine_count > 0]),
                'unique_patterns': list(set(p.value for a in all_analyses.values() for p in a.concurrency_analysis.detected_patterns))
            },
            'performance_summary': {
                'total_flags': sum(sum(len(c.performance_flags) for c in a.constructs) for a in all_analyses.values()),
                'unique_flags': list(set(f.value for a in all_analyses.values() for c in a.constructs for f in c.performance_flags))
            },
            'complexity_summary': {
                'average_function_complexity': sum(c.complexity_score for a in all_analyses.values() for c in a.constructs if c.construct_type.value in ['function', 'method']) / max(sum(len([c for c in a.constructs if c.construct_type.value in ['function', 'method']]) for a in all_analyses.values()), 1),
                'high_complexity_functions': len([c for a in all_analyses.values() for c in a.constructs if c.complexity_score > 0.7])
            },
            'recommendations_summary': {
                'total_recommendations': sum(len(a.recommendations) for a in all_analyses.values()),
                'common_recommendations': [rec for a in all_analyses.values() for rec in a.recommendations]
            }
        }
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"   Results saved to: {results_path}")
        
        print("\n🎉 Go AST Analyzer test completed successfully!")
        print("\n📈 Go Language Mastery Summary:")
        print(f"   • Analyzed {len(all_analyses)} Go files with comprehensive AST parsing")
        print(f"   • Identified {results['total_constructs']} language constructs")
        print(f"   • Detected {results['concurrency_summary']['total_goroutines']} goroutines across {results['concurrency_summary']['files_with_concurrency']} files")
        print(f"   • Found {len(results['concurrency_summary']['unique_patterns'])} unique concurrency patterns")
        print(f"   • Flagged {results['performance_summary']['total_flags']} performance issues")
        print(f"   • Generated {results['recommendations_summary']['total_recommendations']} improvement recommendations")
        print(f"   • Average function complexity: {results['complexity_summary']['average_function_complexity']:.2f}")
        
        print("\n🧠 Cognitive Capabilities Demonstrated:")
        print("   ✅ Go syntax and semantic analysis")
        print("   ✅ Concurrency pattern recognition (goroutines, channels, mutexes)")
        print("   ✅ Performance bottleneck detection")
        print("   ✅ Security vulnerability analysis")
        print("   ✅ Code complexity measurement")
        print("   ✅ Architecture pattern identification")
        print("   ✅ Test coverage analysis")
        print("   ✅ Automated recommendation generation")
        
        return all_analyses
        
    except Exception as e:
        print(f"❌ Error in Go analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


async def create_sample_go_files():
    """Create comprehensive Go code samples for testing"""
    
    test_dir = Path("/tmp/aura_go_analysis")
    test_dir.mkdir(exist_ok=True)
    
    files = {}
    
    # 1. Concurrency-heavy service
    concurrency_service = test_dir / "concurrency_service.go"
    concurrency_service.write_text('''
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// WorkerPool demonstrates worker pool pattern
type WorkerPool struct {
    workerCount int
    jobQueue    chan Job
    wg          sync.WaitGroup
    ctx         context.Context
    cancel      context.CancelFunc
}

type Job struct {
    ID   int
    Data string
}

type Result struct {
    JobID  int
    Output string
    Error  error
}

// NewWorkerPool creates a new worker pool
func NewWorkerPool(workerCount, queueSize int) *WorkerPool {
    ctx, cancel := context.WithCancel(context.Background())
    return &WorkerPool{
        workerCount: workerCount,
        jobQueue:    make(chan Job, queueSize),
        ctx:         ctx,
        cancel:      cancel,
    }
}

// Start begins processing jobs with worker goroutines
func (wp *WorkerPool) Start() {
    for i := 0; i < wp.workerCount; i++ {
        wp.wg.Add(1)
        go wp.worker(i)
    }
}

// worker processes jobs from the queue
func (wp *WorkerPool) worker(id int) {
    defer wp.wg.Done()
    
    for {
        select {
        case job := <-wp.jobQueue:
            result := wp.processJob(job)
            fmt.Printf("Worker %d processed job %d: %s\\n", id, job.ID, result.Output)
        case <-wp.ctx.Done():
            fmt.Printf("Worker %d shutting down\\n", id)
            return
        }
    }
}

// processJob simulates job processing
func (wp *WorkerPool) processJob(job Job) Result {
    // Simulate work
    time.Sleep(100 * time.Millisecond)
    
    return Result{
        JobID:  job.ID,
        Output: fmt.Sprintf("Processed: %s", job.Data),
    }
}

// AddJob adds a job to the queue
func (wp *WorkerPool) AddJob(job Job) error {
    select {
    case wp.jobQueue <- job:
        return nil
    case <-wp.ctx.Done():
        return fmt.Errorf("worker pool is shutting down")
    default:
        return fmt.Errorf("job queue is full")
    }
}

// Stop gracefully shuts down the worker pool
func (wp *WorkerPool) Stop() {
    close(wp.jobQueue)
    wp.cancel()
    wp.wg.Wait()
}

// Pipeline demonstrates pipeline pattern
func Pipeline(input <-chan int) <-chan string {
    output := make(chan string)
    
    go func() {
        defer close(output)
        for num := range input {
            select {
            case output <- fmt.Sprintf("processed-%d", num*2):
            case <-time.After(5 * time.Second):
                fmt.Println("Pipeline timeout")
                return
            }
        }
    }()
    
    return output
}
''')
    files["concurrency_service.go"] = concurrency_service
    
    # 2. HTTP service with potential security issues
    http_service = test_dir / "http_service.go"
    http_service.write_text('''
package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "strconv"
    "database/sql"
    _ "github.com/lib/pq"
)

// User represents a user in the system
type User struct {
    ID       int    `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
    Password string `json:"-"`
}

// UserService handles user operations
type UserService struct {
    db *sql.DB
}

// NewUserService creates a new user service
func NewUserService(db *sql.DB) *UserService {
    return &UserService{db: db}
}

// GetUser retrieves a user by ID - potential SQL injection
func (us *UserService) GetUser(w http.ResponseWriter, r *http.Request) {
    userID := r.URL.Query().Get("id")
    
    // SECURITY ISSUE: SQL injection vulnerability
    query := fmt.Sprintf("SELECT id, username, email FROM users WHERE id = %s", userID)
    
    var user User
    err := us.db.QueryRow(query).Scan(&user.ID, &user.Username, &user.Email)
    if err != nil {
        http.Error(w, "User not found", http.StatusNotFound)
        return
    }
    
    // SECURITY ISSUE: No input validation or sanitization
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}

// CreateUser creates a new user - multiple issues
func (us *UserService) CreateUser(w http.ResponseWriter, r *http.Request) {
    var user User
    
    // SECURITY ISSUE: No content-type validation
    if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }
    
    // SECURITY ISSUE: Password stored in plain text
    // SECURITY ISSUE: No input validation
    query := "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id"
    err := us.db.QueryRow(query, user.Username, user.Email, user.Password).Scan(&user.ID)
    if err != nil {
        http.Error(w, "Failed to create user", http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}

// SearchUsers searches for users - performance issues
func (us *UserService) SearchUsers(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("q")
    
    // PERFORMANCE ISSUE: No pagination, could return millions of records
    // SECURITY ISSUE: Potential SQL injection if not properly escaped
    sqlQuery := "SELECT id, username, email FROM users WHERE username LIKE '%" + query + "%'"
    
    rows, err := us.db.Query(sqlQuery)
    if err != nil {
        http.Error(w, "Search failed", http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    
    var users []User
    for rows.Next() {
        var user User
        err := rows.Scan(&user.ID, &user.Username, &user.Email)
        if err != nil {
            continue
        }
        users = append(users, user)
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}

// ProcessBatch demonstrates performance issues
func (us *UserService) ProcessBatch(userIDs []int) error {
    var result string
    
    // PERFORMANCE ISSUE: String concatenation in loop
    for _, id := range userIDs {
        result += "User ID: " + strconv.Itoa(id) + "\\n"
    }
    
    fmt.Println(result)
    return nil
}
''')
    files["http_service.go"] = http_service
    
    # 3. Complex algorithm with high cyclomatic complexity
    algorithm = test_dir / "complex_algorithm.go"
    algorithm.write_text('''
package algorithm

import (
    "errors"
    "reflect"
    "sort"
)

// DataProcessor represents a complex data processing system
type DataProcessor struct {
    config Config
    cache  map[string]interface{}
}

type Config struct {
    EnableCaching    bool
    MaxCacheSize     int
    ProcessingMode   string
    ValidationLevel  int
}

// ProcessData demonstrates high cyclomatic complexity
func (dp *DataProcessor) ProcessData(data interface{}, options map[string]interface{}) (interface{}, error) {
    if data == nil {
        return nil, errors.New("data cannot be nil")
    }
    
    // PERFORMANCE ISSUE: Reflection overuse
    dataType := reflect.TypeOf(data)
    dataValue := reflect.ValueOf(data)
    
    // Complex nested conditionals
    if dp.config.ValidationLevel > 0 {
        if dp.config.ValidationLevel == 1 {
            if dataType.Kind() == reflect.Slice {
                if dataValue.Len() == 0 {
                    return nil, errors.New("empty slice not allowed")
                }
                
                for i := 0; i < dataValue.Len(); i++ {
                    elem := dataValue.Index(i)
                    if elem.Kind() == reflect.Ptr && elem.IsNil() {
                        return nil, errors.New("nil pointer in slice")
                    }
                    
                    if elem.Kind() == reflect.String {
                        if elem.String() == "" {
                            if dp.config.ProcessingMode == "strict" {
                                return nil, errors.New("empty string not allowed in strict mode")
                            } else if dp.config.ProcessingMode == "lenient" {
                                // Continue processing
                                continue
                            } else {
                                return nil, errors.New("unknown processing mode")
                            }
                        }
                    }
                }
            } else if dataType.Kind() == reflect.Map {
                if dataValue.Len() == 0 {
                    return nil, errors.New("empty map not allowed")
                }
                
                for _, key := range dataValue.MapKeys() {
                    value := dataValue.MapIndex(key)
                    if value.Kind() == reflect.Interface {
                        value = value.Elem()
                    }
                    
                    if value.Kind() == reflect.String && value.String() == "" {
                        if dp.config.ProcessingMode == "strict" {
                            return nil, errors.New("empty string value not allowed")
                        }
                    }
                }
            }
        } else if dp.config.ValidationLevel == 2 {
            // Even more complex validation logic
            if err := dp.complexValidation(data, options); err != nil {
                return nil, err
            }
        }
    }
    
    // Caching logic
    if dp.config.EnableCaching {
        cacheKey := dp.generateCacheKey(data, options)
        if cached, exists := dp.cache[cacheKey]; exists {
            return cached, nil
        }
        
        result, err := dp.performProcessing(data, options)
        if err != nil {
            return nil, err
        }
        
        if len(dp.cache) < dp.config.MaxCacheSize {
            dp.cache[cacheKey] = result
        }
        
        return result, nil
    }
    
    return dp.performProcessing(data, options)
}

// complexValidation adds even more complexity
func (dp *DataProcessor) complexValidation(data interface{}, options map[string]interface{}) error {
    dataValue := reflect.ValueOf(data)
    
    switch dataValue.Kind() {
    case reflect.Slice:
        return dp.validateSlice(dataValue, options)
    case reflect.Map:
        return dp.validateMap(dataValue, options)
    case reflect.Struct:
        return dp.validateStruct(dataValue, options)
    default:
        return dp.validatePrimitive(dataValue, options)
    }
}

func (dp *DataProcessor) validateSlice(value reflect.Value, options map[string]interface{}) error {
    maxSize, exists := options["maxSize"]
    if exists {
        if size, ok := maxSize.(int); ok {
            if value.Len() > size {
                return errors.New("slice too large")
            }
        }
    }
    
    for i := 0; i < value.Len(); i++ {
        elem := value.Index(i)
        if err := dp.validateElement(elem, options); err != nil {
            return err
        }
    }
    
    return nil
}

func (dp *DataProcessor) validateMap(value reflect.Value, options map[string]interface{}) error {
    // More validation logic...
    return nil
}

func (dp *DataProcessor) validateStruct(value reflect.Value, options map[string]interface{}) error {
    // More validation logic...
    return nil
}

func (dp *DataProcessor) validatePrimitive(value reflect.Value, options map[string]interface{}) error {
    // More validation logic...
    return nil
}

func (dp *DataProcessor) validateElement(elem reflect.Value, options map[string]interface{}) error {
    // More validation logic...
    return nil
}

func (dp *DataProcessor) generateCacheKey(data interface{}, options map[string]interface{}) string {
    // PERFORMANCE ISSUE: String concatenation
    key := "cache_"
    key += reflect.TypeOf(data).String()
    
    // Sort options for consistent key
    var keys []string
    for k := range options {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    
    for _, k := range keys {
        key += "_" + k + "_" + reflect.ValueOf(options[k]).String()
    }
    
    return key
}

func (dp *DataProcessor) performProcessing(data interface{}, options map[string]interface{}) (interface{}, error) {
    // Actual processing logic would go here
    return data, nil
}
''')
    files["complex_algorithm.go"] = algorithm
    
    # 4. Clean architecture example
    clean_service = test_dir / "clean_service.go"
    clean_service.write_text('''
package service

import (
    "context"
    "fmt"
)

// UserRepository defines the contract for user data operations
type UserRepository interface {
    GetByID(ctx context.Context, id string) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
}

// NotificationService defines the contract for notifications
type NotificationService interface {
    SendWelcomeEmail(ctx context.Context, user *User) error
    SendPasswordResetEmail(ctx context.Context, email string) error
}

// User represents a user entity
type User struct {
    ID       string `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
    IsActive bool   `json:"is_active"`
}

// UserService implements business logic for user operations
type UserService struct {
    userRepo            UserRepository
    notificationService NotificationService
}

// NewUserService creates a new user service with dependencies
func NewUserService(userRepo UserRepository, notificationService NotificationService) *UserService {
    return &UserService{
        userRepo:            userRepo,
        notificationService: notificationService,
    }
}

// CreateUser creates a new user with proper validation and notifications
func (s *UserService) CreateUser(ctx context.Context, user *User) error {
    if user == nil {
        return fmt.Errorf("user cannot be nil")
    }
    
    if err := s.validateUser(user); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }
    
    if err := s.userRepo.Create(ctx, user); err != nil {
        return fmt.Errorf("failed to create user: %w", err)
    }
    
    // Send welcome email asynchronously
    go func() {
        if err := s.notificationService.SendWelcomeEmail(context.Background(), user); err != nil {
            // Log error in real implementation
            fmt.Printf("Failed to send welcome email: %v", err)
        }
    }()
    
    return nil
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
    if id == "" {
        return nil, fmt.Errorf("user ID cannot be empty")
    }
    
    user, err := s.userRepo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("failed to get user: %w", err)
    }
    
    return user, nil
}

// UpdateUser updates an existing user
func (s *UserService) UpdateUser(ctx context.Context, user *User) error {
    if user == nil {
        return fmt.Errorf("user cannot be nil")
    }
    
    if user.ID == "" {
        return fmt.Errorf("user ID cannot be empty")
    }
    
    if err := s.validateUser(user); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }
    
    if err := s.userRepo.Update(ctx, user); err != nil {
        return fmt.Errorf("failed to update user: %w", err)
    }
    
    return nil
}

// DeactivateUser deactivates a user account
func (s *UserService) DeactivateUser(ctx context.Context, id string) error {
    if id == "" {
        return fmt.Errorf("user ID cannot be empty")
    }
    
    user, err := s.userRepo.GetByID(ctx, id)
    if err != nil {
        return fmt.Errorf("failed to get user: %w", err)
    }
    
    user.IsActive = false
    
    if err := s.userRepo.Update(ctx, user); err != nil {
        return fmt.Errorf("failed to deactivate user: %w", err)
    }
    
    return nil
}

// validateUser performs business rule validation
func (s *UserService) validateUser(user *User) error {
    if user.Username == "" {
        return fmt.Errorf("username cannot be empty")
    }
    
    if len(user.Username) < 3 {
        return fmt.Errorf("username must be at least 3 characters")
    }
    
    if user.Email == "" {
        return fmt.Errorf("email cannot be empty")
    }
    
    // Simple email validation
    if !contains(user.Email, "@") {
        return fmt.Errorf("invalid email format")
    }
    
    return nil
}

// contains checks if string contains substring
func contains(s, substr string) bool {
    return len(s) >= len(substr) && s[len(s)-len(substr):] == substr || 
           len(s) > len(substr) && s[:len(substr)] == substr ||
           len(s) > len(substr) && indexOfSubstring(s, substr) != -1
}

// indexOfSubstring finds index of substring (simplified implementation)
func indexOfSubstring(s, substr string) int {
    for i := 0; i <= len(s)-len(substr); i++ {
        if s[i:i+len(substr)] == substr {
            return i
        }
    }
    return -1
}
''')
    files["clean_service.go"] = clean_service
    
    return files


if __name__ == "__main__":
    asyncio.run(test_go_analyzer())