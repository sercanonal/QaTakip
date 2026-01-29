import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { CheckSquare, User, ArrowRight, Loader2, Mail } from "lucide-react";

const Login = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();
    
    if (!trimmedUsername) {
      toast.error("Lütfen kullanıcı adınızı girin");
      return;
    }
    
    if (!trimmedEmail) {
      toast.error("Lütfen email adresinizi girin");
      return;
    }
    
    if (trimmedUsername.length < 2) {
      toast.error("Kullanıcı adı en az 2 karakter olmalı");
      return;
    }

    setLoading(true);
    try {
      await register(trimmedUsername, trimmedEmail);
      toast.success("Hoş geldiniz!");
    } catch (error) {
      const message = error.userMessage || error.response?.data?.detail || "Bir hata oluştu";
      toast.error(message);
      console.error("Login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md animate-fadeIn">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/30">
            <CheckSquare className="w-7 h-7 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-heading text-2xl font-bold">QA Task Manager</h1>
            <p className="text-sm text-muted-foreground">Intertech QA Ekibi</p>
          </div>
        </div>

        <Card className="border-border/50 bg-card shadow-2xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="font-heading text-2xl">
              Başlayalım
            </CardTitle>
            <CardDescription>
              Kullanıcı bilgileriniz ile giriş yapın
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Intertech Kullanıcı Adı</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="SERCANO"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-10 h-12 bg-secondary/50 border-border/50 focus:border-primary"
                    autoFocus
                    required
                    minLength={2}
                    maxLength={50}
                    data-testid="username-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Intertech Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="kullanici@intertech.com.tr"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 h-12 bg-secondary/50 border-border/50 focus:border-primary"
                    required
                    data-testid="email-input"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-12 btn-glow font-semibold"
                disabled={loading}
                data-testid="submit-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Giriş Yap
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          © 2025 Intertech QA Task Manager
        </p>
      </div>
    </div>
  );
};

export default Login;
