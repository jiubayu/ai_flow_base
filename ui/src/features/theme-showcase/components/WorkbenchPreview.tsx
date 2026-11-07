import { Badge } from "@/shared/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { FilterChip } from "@/shared/components/theme/FilterChip";
import { NavItem } from "@/shared/components/theme/NavItem";
import { ThemeShowcaseShell } from "./ThemeShowcaseShell";

export function WorkbenchPreview() {
  return (
    <ThemeShowcaseShell
      title="工作台式布局"
      subtitle="顶部导航 + 筛选栏 + 卡片网格 + 信息列表的组合样例，验证页面骨架风格一致。"
    >
      <div className="surface-page rounded-md p-t-4">
        <nav className="flex items-center justify-between gap-t-3 border-b border-edge-weak pb-t-3">
          <span className="text-level-2">AI-Flow</span>
          <div className="flex gap-t-1">
            <NavItem active>工作区</NavItem>
            <NavItem>任务</NavItem>
            <NavItem>设置</NavItem>
          </div>
        </nav>
        <div className="mt-t-3 flex flex-wrap gap-t-2">
          <FilterChip active>全部</FilterChip>
          <FilterChip>运行中</FilterChip>
          <FilterChip>已完成</FilterChip>
        </div>
        <div className="mt-t-3 grid gap-t-3 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>数据摄取</CardTitle>
              <Badge variant="positive">运行中</Badge>
            </CardHeader>
            <CardContent>卡片网格中的信息块，消费面板层级与状态强调色。</CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>主题基线</CardTitle>
              <Badge variant="warning">待评审</Badge>
            </CardHeader>
            <CardContent>同一页面内圆角、边框强度与阴影语言保持一致。</CardContent>
          </Card>
        </div>
        <div className="surface-overlay mt-t-3 p-t-3">
          <p className="text-level-3">信息列表块：浮层容器承载，文本层级清晰。</p>
          <p className="mt-t-1 text-level-4">次级说明文字来自 content-muted / caption 字号。</p>
        </div>
      </div>
    </ThemeShowcaseShell>
  );
}
