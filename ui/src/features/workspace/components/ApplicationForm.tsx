import { type FormEvent, type Ref, useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Input } from "@/shared/components/ui/input";

const NAME_MAX = 80;
const DESCRIPTION_MAX = 500;

interface ApplicationFormProps {
  mode: "create" | "edit";
  initialName?: string;
  initialDescription?: string;
  /** 返回 true 表示提交成功；服务端错误由调用方通过 error 回传。 */
  onSubmit: (name: string, description: string) => Promise<boolean>;
  onCancel?: () => void;
  error?: string | null;
  nameInputRef?: Ref<HTMLInputElement>;
}

interface FieldErrors {
  name?: string;
  description?: string;
}

function validate(name: string, description: string): FieldErrors {
  const errors: FieldErrors = {};
  const trimmedName = name.trim();
  if (trimmedName.length === 0) {
    errors.name = "应用名称不能为空";
  } else if (trimmedName.length > NAME_MAX) {
    errors.name = `应用名称不能超过 ${NAME_MAX} 个字符`;
  }
  if (description.length > DESCRIPTION_MAX) {
    errors.description = `应用描述不能超过 ${DESCRIPTION_MAX} 个字符`;
  }
  return errors;
}

export function ApplicationForm({
  mode,
  initialName = "",
  initialDescription = "",
  onSubmit,
  onCancel,
  error,
  nameInputRef,
}: ApplicationFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [succeeded, setSucceeded] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const errors = validate(name, description);
    setFieldErrors(errors);
    if (errors.name || errors.description) {
      return;
    }
    setSubmitting(true);
    setSucceeded(false);
    const ok = await onSubmit(name.trim(), description);
    setSubmitting(false);
    setSucceeded(ok);
    if (ok && mode === "create") {
      setName("");
      setDescription("");
    }
  };

  const nameId = `application-name-${mode}`;
  const descriptionId = `application-description-${mode}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{mode === "create" ? "创建应用" : "编辑应用"}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-t-3">
          <div className="flex flex-col gap-t-1">
            <label htmlFor={nameId} className="text-caption text-content-secondary">
              应用名称（1-{NAME_MAX} 个字符）
            </label>
            <Input
              id={nameId}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如：客服自动回复流程"
              maxLength={NAME_MAX}
              required
              ref={nameInputRef}
            />
            {fieldErrors.name && (
              <p className="text-caption text-content-accent" role="alert">
                {fieldErrors.name}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-t-1">
            <label htmlFor={descriptionId} className="text-caption text-content-secondary">
              应用描述（可选，最多 {DESCRIPTION_MAX} 字符）
            </label>
            <textarea
              id={descriptionId}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={DESCRIPTION_MAX}
              rows={3}
              className="field-focus w-full rounded-md border border-edge-base bg-surface-panel px-t-3 py-t-2 text-body-sm text-content-primary placeholder:text-content-muted"
            />
            {fieldErrors.description && (
              <p className="text-caption text-content-accent" role="alert">
                {fieldErrors.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-t-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? "提交中…" : mode === "create" ? "创建" : "保存"}
            </Button>
            {onCancel && (
              <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
                取消
              </Button>
            )}
            {succeeded && (
              <span className="text-caption text-accent-positive" role="status">
                已保存
              </span>
            )}
          </div>

          {error && (
            <p className="text-caption text-content-accent" role="alert">
              {error}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
