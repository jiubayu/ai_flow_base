import { Badge, type BadgeProps } from "@/shared/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";

interface StatusCardProps {
  title: string;
  state: string;
  message?: string;
}

const stateVariant: Record<string, BadgeProps["variant"]> = {
  ok: "positive",
  running: "positive",
  SUCCESS: "positive",
  PENDING: "warning",
  STARTED: "warning",
  FAILURE: "negative",
  error: "negative",
};

export function StatusCard({ title, state, message }: StatusCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <Badge variant={stateVariant[state] ?? "neutral"}>{state}</Badge>
      </CardHeader>
      {message ? <CardContent>{message}</CardContent> : null}
    </Card>
  );
}
