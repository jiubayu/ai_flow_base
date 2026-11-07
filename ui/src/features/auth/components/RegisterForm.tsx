import { type FormEvent, useEffect, useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";
import type { AuthController } from "../hooks/useAuthSession";

export function RegisterForm({ auth }: { auth: AuthController }) {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [sending, setSending] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [retryAfter, setRetryAfter] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (retryAfter <= 0) return;
    const timer = setInterval(() => setRetryAfter((value) => (value > 0 ? value - 1 : 0)), 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  const handleSendCode = async () => {
    setSending(true);
    setError(null);
    try {
      const accepted = await auth.sendCode(email);
      setNotice(`验证码已发送，请在 ${accepted.expires_in_seconds} 秒内完成注册`);
      setRetryAfter(accepted.retry_after_seconds);
    } catch (err) {
      setError(String(err));
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await auth.registerAccount(email, code, password);
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>注册账号</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-t-3">
          <Input
            type="email"
            placeholder="邮箱"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <div className="flex items-center gap-t-2">
            <Input
              inputMode="numeric"
              pattern="[0-9]{6}"
              placeholder="6 位验证码"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              required
            />
            <Button type="button" variant="secondary" size="md" onClick={handleSendCode} disabled={sending || retryAfter > 0}>
              {retryAfter > 0 ? `重新发送（${retryAfter}s）` : "发送验证码"}
            </Button>
          </div>
          <Input
            type="password"
            placeholder="密码（至少 8 位，含字母和数字）"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <Button type="submit" disabled={submitting}>
            {submitting ? "注册中…" : "注册并自动登录"}
          </Button>
          {notice && <p className="text-caption text-content-secondary">{notice}</p>}
          {error && <p className="text-caption text-content-accent">{error}</p>}
        </form>
      </CardContent>
    </Card>
  );
}
