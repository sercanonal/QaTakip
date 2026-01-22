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
  ListTodo
} from "lucide-react";
import { cn } from "../lib/utils";
import { format, isSameDay, startOfMonth, endOfMonth, eachDayOfInterval, isToday, addMonths, subMonths } from "date-fns";
import { tr } from "date-fns/locale";

const statusLabels = {
  todo: "Yapılacak",
  in_progress: "Devam Ediyor",
  completed: "Tamamlandı"
};

const statusColors = {
  todo: "bg-muted text-muted-foreground",
  in_progress: "bg-info/20 text-info",
  completed: "bg-success/20 text-success"
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

  const getTasksForDate = (date) => {
    return tasks.filter(task => {
      if (!task.due_date) return false;
      return isSameDay(new Date(task.due_date), date);
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

  // Get days with tasks for the current month
  const daysWithTasks = tasks
    .filter(t => t.due_date)
    .map(t => new Date(t.due_date));

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
        <p className="text-muted-foreground">Görevlerinizi tarih bazında görüntüleyin</p>
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
                caption_label: "text-sm font-medium",
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
                day_disabled: "text-muted-foreground opacity-50",
              }}
              components={{
                DayContent: ({ date }) => {
                  const dayTasks = getTasksForDate(date);
                  return (
                    <div className="flex flex-col items-center justify-center h-full">
                      <span>{format(date, "d")}</span>
                      {dayTasks.length > 0 && (
                        <div className="flex gap-0.5 mt-1">
                          {dayTasks.slice(0, 3).map((task, i) => (
                            <div
                              key={i}
                              className="w-1.5 h-1.5 rounded-full"
                              style={{ backgroundColor: getCategoryColor(task.category_id) }}
                            />
                          ))}
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
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {selectedDateTasks.length} görev
            </p>
          </CardHeader>
          <CardContent>
            {selectedDateTasks.length > 0 ? (
              <div className="space-y-3">
                {selectedDateTasks.map((task) => (
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
                      <Badge className={cn("text-xs shrink-0", statusColors[task.status])}>
                        {task.status === "todo" && <ListTodo className="w-3 h-3 mr-1" />}
                        {task.status === "in_progress" && <Clock className="w-3 h-3 mr-1" />}
                        {task.status === "completed" && <CheckCircle2 className="w-3 h-3 mr-1" />}
                        {statusLabels[task.status]}
                      </Badge>
                    </div>
                  </div>
                ))}
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

      {/* Upcoming Tasks */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="font-heading flex items-center gap-2">
            <Clock className="w-5 h-5 text-warning" />
            Yaklaşan Görevler
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.filter(t => t.due_date && new Date(t.due_date) >= new Date() && t.status !== "completed").length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {tasks
                .filter(t => t.due_date && new Date(t.due_date) >= new Date() && t.status !== "completed")
                .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
                .slice(0, 6)
                .map((task) => (
                  <div
                    key={task.id}
                    className="p-3 rounded-lg bg-secondary/30 border border-border/50"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: getCategoryColor(task.category_id) }}
                      />
                      <span className="text-xs text-muted-foreground font-mono">
                        {format(new Date(task.due_date), "d MMM", { locale: tr })}
                      </span>
                    </div>
                    <p className="font-medium text-sm">{task.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {getCategoryName(task.category_id)}
                    </p>
                  </div>
                ))}
            </div>
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              <p>Yaklaşan görev yok</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CalendarPage;
