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
  AlertOctagon
} from "lucide-react";
import { cn } from "../lib/utils";
import { format, isSameDay, isToday, addMonths, subMonths, startOfDay } from "date-fns";
import { tr } from "date-fns/locale";

const statusConfig = {
  todo: { label: "Yapılacak", icon: ListTodo, color: "bg-muted text-muted-foreground" },
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
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await api.get("/tasks");
      setTasks(response.data);
    } catch (error) {
      console.error("Error fetching tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  // Get tasks for a specific date
  // Shows tasks if:
  // 1. due_date matches the date, OR
  // 2. task is active (todo/in_progress/blocked) AND date is today
  const getTasksForDate = (date) => {
    const isSelectedToday = isToday(date);
    
    return tasks.filter(task => {
      // If task has due_date and it matches
      if (task.due_date && isSameDay(new Date(task.due_date), date)) {
        return true;
      }
      
      // If date is today, show all active (non-completed) tasks
      if (isSelectedToday && task.status !== "completed") {
        return true;
      }
      
      return false;
    });
  };

  // Get days that have tasks (for calendar dots)
  const getDaysWithTasks = () => {
    const days = new Set();
    const today = startOfDay(new Date());
    
    tasks.forEach(task => {
      // Add due_date
      if (task.due_date) {
        days.add(startOfDay(new Date(task.due_date)).toISOString());
      }
      
      // Add today if task is active
      if (task.status !== "completed") {
        days.add(today.toISOString());
      }
    });
    
    return days;
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
  const daysWithTasksSet = getDaysWithTasks();
  const isSelectedToday = isToday(selectedDate);

  // Sort tasks: active first, then by priority
  const sortedTasks = [...selectedDateTasks].sort((a, b) => {
    const statusOrder = { blocked: 0, in_progress: 1, todo: 2, completed: 3 };
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    
    if (statusOrder[a.status] !== statusOrder[b.status]) {
      return statusOrder[a.status] - statusOrder[b.status];
    }
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

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
      <div>
        <h2 className="font-heading text-2xl font-bold">Takvim</h2>
        <p className="text-muted-foreground">
          {isSelectedToday 
            ? "Bugünkü görevleriniz ve yaklaşan deadlinelar"
            : "Seçili tarihteki görevler"
          }
        </p>
      </div>

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
                  const hasActiveTasks = dayTasks.some(t => t.status !== "completed");
                  const hasBlockedTasks = dayTasks.some(t => t.status === "blocked");
                  
                  return (
                    <div className="flex flex-col items-center justify-center h-full">
                      <span>{format(date, "d")}</span>
                      {dayTasks.length > 0 && (
                        <div className="flex gap-0.5 mt-1">
                          {hasBlockedTasks && (
                            <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                          )}
                          {hasActiveTasks && !hasBlockedTasks && (
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          )}
                          {dayTasks.length > 1 && (
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
              {isSelectedToday && " (aktif görevler dahil)"}
            </p>
          </CardHeader>
          <CardContent>
            {sortedTasks.length > 0 ? (
              <div className="space-y-3">
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
                          {task.due_date && !isSelectedToday && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Deadline: {format(new Date(task.due_date), "d MMM", { locale: tr })}
                            </p>
                          )}
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

      {/* Daily Summary for Today */}
      {isSelectedToday && (
        <Card className="border-border/50 bg-card">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Daily Özeti
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(statusConfig).map(([status, config]) => {
                const count = tasks.filter(t => t.status === status).length;
                const StatusIcon = config.icon;
                return (
                  <div key={status} className={cn(
                    "p-4 rounded-lg text-center",
                    config.color.replace("text-", "bg-").split(" ")[0]
                  )}>
                    <StatusIcon className="w-6 h-6 mx-auto mb-2" />
                    <p className="text-2xl font-heading font-bold">{count}</p>
                    <p className="text-xs">{config.label}</p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CalendarPage;
