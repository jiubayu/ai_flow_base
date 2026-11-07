import { Button } from "@/shared/components/ui/button";
import { EmptyState } from "@/shared/components/theme/EmptyState";

export function WorkspaceEmptyState({ onCreateEntry }: { onCreateEntry: () => void }) {
  return (
    <EmptyState
      title="还没有应用"
      description="创建第一个应用后，卡片会立即出现在这里，无需刷新页面。"
      action={
        <Button size="sm" onClick={onCreateEntry}>
          创建应用
        </Button>
      }
    />
  );
}
