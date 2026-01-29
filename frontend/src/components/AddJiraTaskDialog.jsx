import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Plus, ExternalLink, Loader2 } from "lucide-react";
import { toast } from "sonner";

const AddJiraTaskDialog = ({ onTaskAdded }) => {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    jira_key: "",
    summary: "",
    description: "",
    status: "backlog",
    priority: "medium",
    jira_url: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.jira_key || !formData.summary) {
      toast.error("Jira Key ve Summary alanları zorunludur");
      return;
    }

    setLoading(true);
    try {
      // Manuel olarak Jira task ekle
      const response = await api.post("/jira/manual-add", {
        user_id: user.id,
        jira_key: formData.jira_key.trim(),
        summary: formData.summary.trim(),
        description: formData.description.trim(),
        status: formData.status,
        priority: formData.priority,
        jira_url: formData.jira_url.trim() || `https://jira.intertech.com.tr/browse/${formData.jira_key.trim()}`
      });

      toast.success("Jira task'ı eklendi!");
      setOpen(false);
      setFormData({
        jira_key: "",
        summary: "",
        description: "",
        status: "backlog",
        priority: "medium",
        jira_url: ""
      });
      
      if (onTaskAdded) {
        onTaskAdded(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Task eklenemedi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Plus className="w-4 h-4" />
          Manuel Jira Task Ekle
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Jira Task Ekle</DialogTitle>
          <DialogDescription>
            Jira'dan manuel olarak task ekleyin (VPN sorunları için)
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="jira_key">Jira Key *</Label>
            <Input
              id="jira_key"
              placeholder="PROJ-123"
              value={formData.jira_key}
              onChange={(e) => setFormData({ ...formData, jira_key: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="summary">Summary *</Label>
            <Input
              id="summary"
              placeholder="Task başlığı"
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Task açıklaması"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Öncelik</Label>
              <Select
                value={formData.priority}
                onValueChange={(value) => setFormData({ ...formData, priority: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Düşük</SelectItem>
                  <SelectItem value="medium">Orta</SelectItem>
                  <SelectItem value="high">Yüksek</SelectItem>
                  <SelectItem value="critical">Kritik</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Durum</Label>
              <Select
                value={formData.status}
                onValueChange={(value) => setFormData({ ...formData, status: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="backlog">Backlog</SelectItem>
                  <SelectItem value="today_planned">Bugün Planlandı</SelectItem>
                  <SelectItem value="in_progress">Devam Ediyor</SelectItem>
                  <SelectItem value="blocked">Bloke</SelectItem>
                  <SelectItem value="completed">Tamamlandı</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="jira_url">Jira URL (Opsiyonel)</Label>
            <div className="relative">
              <Input
                id="jira_url"
                placeholder="https://jira.intertech.com.tr/browse/PROJ-123"
                value={formData.jira_url}
                onChange={(e) => setFormData({ ...formData, jira_url: e.target.value })}
              />
              {formData.jira_url && (
                <a
                  href={formData.jira_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <ExternalLink className="w-4 h-4 text-muted-foreground hover:text-foreground" />
                </a>
              )}
            </div>
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              İptal
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Ekleniyor...
                </>
              ) : (
                "Task Ekle"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AddJiraTaskDialog;
