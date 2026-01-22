import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Calendar } from "../components/ui/calendar";
import { 
  ChevronLeft, 
  ChevronRight,
  CalendarDays,
  Clock,
  CheckCircle2,
  ListTodo,
  AlertOctagon,
  Copy,
  MessageSquare
} from "lucide-react";
import { cn } from "../lib/utils";
import { format, isSameDay, isToday, addMonths, subMonths, startOfDay } from "date-fns";
import { tr } from "date-fns/locale";
import { toast } from "sonner";

const statusConfig = {
  todo: { label: "Yapılacak", icon: ListTodo, color: "bg-zinc-500/20 text-zinc-400" },
  in_progress: { label: "Devam Ediyor", icon: Clock, color: "bg-blue-500/20 text-blue-400" },
  blocked: { label: "Bloke", icon: AlertOctagon, color: "bg-orange-500/20 text-orange-400" },
  completed: { label: "Tamamlandı", icon: CheckCircle2, color: "bg-green-500/20 text-green-400" }
};

const priorityColors = {
  low: "border-muted-foreground",
  medium: "border-warning",
  high: "border-primary",
  critical: "border-destructive"
};

const CalendarPage = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [dailySummary, setDailySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [tasksRes, summaryRes] = await Promise.all([
        api.get("/tasks"),
        api.get("/daily-summary")
      ]);
      setTasks(tasksRes.data);
      setDailySummary(summaryRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getTasksForDate = (date) => {
    const isSelectedToday = isToday(date);
    
    return tasks.filter(task => {
      if (task.due_date && isSameDay(new Date(task.due_date), date)) {
        return true;
      }
      if (isSelectedToday && task.status !== "completed") {
        return true;
      }
      return false;
    });
  };

  const getCategoryColor = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.color || "#3B82F6";
  };

  const getCategoryName = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.name || categoryId;
  };

  const selectedDateTasks = getTasksForDate(selectedDate);
  const isSelectedToday = isToday(selectedDate);

  const sortedTasks = [...selectedDateTasks].sort((a, b) => {
    const statusOrder = { blocked: 0, in_progress: 1, todo: 2, completed: 3 };
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    
    if (statusOrder[a.status] !== statusOrder[b.status]) {
      return statusOrder[a.status] - statusOrder[b.status];
    }
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  // Generate daily standup text
  const generateDailyText = () => {
    if (!dailySummary) return "";
    
    let text = "📋 Daily Standup\n\n";
    
    // Yesterday
    if (dailySummary.yesterday_completed.length > 0) {
      text += "✅ Dün tamamladım:\n";
      dailySummary.yesterday_completed.forEach(task => {
        const project = task.project_name ? ` (${task.project_name})` : "";
        text += `  • ${task.title}${project}\n`;
      });
      text += "\n";
    } else {
      text += "✅ Dün tamamlanan görev yok\n\n";
    }
    
    // Today - In Progress
    if (dailySummary.today_in_progress.length > 0) {
      text += "🔄 Bugün devam edeceğim:\n";
      dailySummary.today_in_progress.forEach(task => {
        const project = task.project_name ? ` (${task.project_name})` : "";
        text += `  • ${task.title}${project}\n`;
      });
      text += "\n";
    }
    
    // Today - Planned
    if (dailySummary.today_planned.length > 0) {
      text += "📌 Bugün başlayacağım:\n";
      dailySummary.today_planned.forEach(task => {
        const project = task.project_name ? ` (${task.project_name})` : "";
        text += `  • ${task.title}${project}\n`;
      });
      text += "\n";
    }
    
    // Blocked
    if (dailySummary.blocked_tasks.length > 0) {
      text += "🚫 Bloke olan:\n";
      dailySummary.blocked_tasks.forEach(task => {
        const project = task.project_name ? ` (${task.project_name})` : "";
        text += `  • ${task.title}${project}\n`;
      });
    }
    
    return text.trim();
  };

  const copyDailyText = async () => {
    const text = generateDailyText();
    
    // Try modern Clipboard API first, then fallback to textarea method
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
      }
      toast.success("Daily metni kopyalandı!");
    } catch (error) {
      console.error("Copy error:", error);
      // Final fallback - show text in a prompt
      toast.info("Metni manuel olarak kopyalayın", {
        description: "Ctrl+A ile seçip Ctrl+C ile kopyalayın",
        duration: 5000
      });
      // Create a modal or prompt with the text
      const modal = document.createElement("div");
      modal.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;">
          <div style="background:#1a1a1a;border-radius:8px;padding:20px;max-width:500px;max-height:80vh;overflow:auto;">
            <h3 style="color:white;margin-bottom:10px;">Daily Metni</h3>
            <textarea style="width:100%;min-height:200px;background:#2a2a2a;color:white;border:1px solid #444;border-radius:4px;padding:10px;" readonly>${text}</textarea>
            <button onclick="this.parentElement.parentElement.remove()" style="margin-top:10px;padding:8px 16px;background:#e91e63;color:white;border:none;border-radius:4px;cursor:pointer;">Kapat</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-bold">Takvim</h2>
          <p className="text-muted-foreground">
            {isSelectedToday 
              ? "Bugünkü görevleriniz ve daily özeti"
              : "Seçili tarihteki görevler"
            }
          </p>
        </div>
        {isSelectedToday && (
          <Button onClick={copyDailyText} className="gap-2" data-testid="copy-daily-btn">
            <Copy className="w-4 h-4" />
            Daily Metnini Kopyala
          </Button>
        )}
      </div>

      {/* Daily Standup Card - Only for Today */}
      {isSelectedToday && dailySummary && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              Daily Standup Özeti
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Yesterday Completed */}
              <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <h4 className="font-semibold text-green-400">Dün Tamamladım</h4>
                </div>
                {dailySummary.yesterday_completed.length > 0 ? (
                  <ul className="space-y-2">
                    {dailySummary.yesterday_completed.slice(0, 5).map(task => (
                      <li key={task.id} className="text-sm">
                        <span className="font-medium">{task.title}</span>
                        {task.project_name && (
                          <span className="text-muted-foreground text-xs block">{task.project_name}</span>
                        )}
                      </li>
                    ))}
                    {dailySummary.yesterday_completed.length > 5 && (
                      <li className="text-xs text-muted-foreground">
                        +{dailySummary.yesterday_completed.length - 5} daha
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">Tamamlanan görev yok</p>
                )}
              </div>

              {/* Today In Progress */}
              <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <h4 className="font-semibold text-blue-400">Bugün Devam Edeceğim</h4>
                </div>
                {dailySummary.today_in_progress.length > 0 ? (
                  <ul className="space-y-2">
                    {dailySummary.today_in_progress.slice(0, 5).map(task => (
                      <li key={task.id} className="text-sm">
                        <span className="font-medium">{task.title}</span>
                        {task.project_name && (
                          <span className="text-muted-foreground text-xs block">{task.project_name}</span>
                        )}
                      </li>
                    ))}
                    {dailySummary.today_in_progress.length > 5 && (
                      <li className="text-xs text-muted-foreground">
                        +{dailySummary.today_in_progress.length - 5} daha
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">Devam eden görev yok</p>
                )}
              </div>

              {/* Today Planned */}
              <div className="p-4 rounded-lg bg-zinc-500/10 border border-zinc-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <ListTodo className="w-5 h-5 text-zinc-400" />
                  <h4 className="font-semibold text-zinc-400">Bugün Başlayacağım</h4>
                </div>
                {dailySummary.today_planned.length > 0 ? (
                  <ul className="space-y-2">
                    {dailySummary.today_planned.slice(0, 5).map(task => (
                      <li key={task.id} className="text-sm">
                        <span className="font-medium">{task.title}</span>
                        {task.project_name && (
                          <span className="text-muted-foreground text-xs block">{task.project_name}</span>
                        )}
                      </li>
                    ))}
                    {dailySummary.today_planned.length > 5 && (
                      <li className="text-xs text-muted-foreground">
                        +{dailySummary.today_planned.length - 5} daha
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">Planlanan görev yok</p>
                )}
              </div>

              {/* Blocked */}
              <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <AlertOctagon className="w-5 h-5 text-orange-400" />
                  <h4 className="font-semibold text-orange-400">Bloke Olan</h4>
                </div>
                {dailySummary.blocked_tasks.length > 0 ? (
                  <ul className="space-y-2">
                    {dailySummary.blocked_tasks.slice(0, 5).map(task => (
                      <li key={task.id} className="text-sm">
                        <span className="font-medium">{task.title}</span>
                        {task.project_name && (
                          <span className="text-muted-foreground text-xs block">{task.project_name}</span>
                        )}
                      </li>
                    ))}
                    {dailySummary.blocked_tasks.length > 5 && (
                      <li className="text-xs text-muted-foreground">
                        +{dailySummary.blocked_tasks.length - 5} daha
                      </li>
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">Bloke görev yok ✓</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-2 border-border/50 bg-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="font-heading flex items-center gap-2">
              <CalendarDays className="w-5 h-5 text-primary" />
              {format(currentMonth, "MMMM yyyy", { locale: tr })}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                data-testid="calendar-prev-month"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setCurrentMonth(new Date());
                  setSelectedDate(new Date());
                }}
                data-testid="calendar-today"
              >
                Bugün
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                data-testid="calendar-next-month"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              month={currentMonth}
              onMonthChange={setCurrentMonth}
              className="rounded-md border-0"
              classNames={{
                months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                month: "space-y-4 w-full",
                caption: "hidden",
                nav: "hidden",
                table: "w-full border-collapse space-y-1",
                head_row: "flex w-full",
                head_cell: "text-muted-foreground rounded-md w-full font-normal text-[0.8rem]",
                row: "flex w-full mt-2",
                cell: cn(
                  "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 w-full",
                  "[&:has([aria-selected])]:bg-primary/10 [&:has([aria-selected])]:rounded-md"
                ),
                day: cn(
                  "h-12 w-full p-0 font-normal aria-selected:opacity-100 hover:bg-secondary rounded-md transition-colors"
                ),
                day_selected: "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground",
                day_today: "bg-accent text-accent-foreground ring-2 ring-primary/50",
                day_outside: "text-muted-foreground opacity-50",
              }}
              components={{
                DayContent: ({ date }) => {
                  const dayTasks = getTasksForDate(date);
                  const hasBlockedTasks = dayTasks.some(t => t.status === "blocked");
                  const hasInProgress = dayTasks.some(t => t.status === "in_progress");
                  
                  return (
                    <div className="flex flex-col items-center justify-center h-full">
                      <span>{format(date, "d")}</span>
                      {dayTasks.length > 0 && (
                        <div className="flex gap-0.5 mt-1">
                          {hasBlockedTasks && (
                            <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                          )}
                          {hasInProgress && (
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          )}
                          {dayTasks.length > 2 && (
                            <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                          )}
                        </div>
                      )}
                    </div>
                  );
                }
              }}
            />
          </CardContent>
        </Card>

        {/* Selected Day Tasks */}
        <Card className="border-border/50 bg-card">
          <CardHeader>
            <CardTitle className="font-heading text-base">
              {format(selectedDate, "d MMMM yyyy, EEEE", { locale: tr })}
              {isSelectedToday && (
                <Badge className="ml-2 bg-primary/20 text-primary">Bugün</Badge>
              )}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {sortedTasks.length} görev
            </p>
          </CardHeader>
          <CardContent>
            {sortedTasks.length > 0 ? (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {sortedTasks.map((task) => {
                  const StatusIcon = statusConfig[task.status]?.icon || ListTodo;
                  return (
                    <div
                      key={task.id}
                      className={cn(
                        "p-3 rounded-lg bg-secondary/30 border-l-2",
                        priorityColors[task.priority]
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className={cn(
                            "font-medium text-sm",
                            task.status === "completed" && "line-through text-muted-foreground"
                          )}>
                            {task.title}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {getCategoryName(task.category_id)}
                          </p>
                        </div>
                        <Badge className={cn("text-xs shrink-0", statusConfig[task.status]?.color)}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusConfig[task.status]?.label}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <CalendarDays className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p className="text-sm">Bu tarihte görev yok</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CalendarPage;
