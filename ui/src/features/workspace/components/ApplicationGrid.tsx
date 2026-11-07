import type { ApplicationCard as ApplicationCardData } from "../api";
import { ApplicationCard } from "./ApplicationCard";

export function ApplicationGrid({
  applications,
  onOpen,
}: {
  applications: ApplicationCardData[];
  onOpen: (applicationId: string) => void;
}) {
  return (
    <ul className="grid grid-cols-1 gap-t-3 sm:grid-cols-2" aria-label="应用卡片列表">
      {applications.map((application) => (
        <li key={application.application_id}>
          <ApplicationCard application={application} onOpen={onOpen} />
        </li>
      ))}
    </ul>
  );
}
