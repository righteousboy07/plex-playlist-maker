import Foundation

@MainActor
final class StoreAutomationScheduler {
    static let shared = StoreAutomationScheduler()

    private var task: Task<Void, Never>?
    private let defaults = UserDefaults.standard
    private let lastRunPrefix = "plexCurator.storeAutomation.lastRun."

    private init() {}

    func start(api: APIClient) {
        guard BuildFlavor.current.isAppStore else { return }
        guard task == nil else { return }

        task = Task { [weak self] in
            guard let self else { return }

            while !Task.isCancelled {
                await self.runDueJobs(api: api)

                do {
                    try await Task.sleep(nanoseconds: 60_000_000_000)
                } catch {
                    break
                }
            }
        }
    }

    func stop() {
        task?.cancel()
        task = nil
    }

    private func runDueJobs(api: APIClient) async {
        StoreAutomationManager.shared.refresh()
        guard StoreAutomationManager.shared.enabled else { return }

        do {
            let jobs = try await api.storeAutomationJobs()
            let now = Date()
            let calendar = Calendar.current

            for job in jobs where isDue(job, at: now, calendar: calendar) {
                let key = runKey(for: job, at: now, calendar: calendar)
                guard defaults.string(forKey: lastRunPrefix + job.name) != key else {
                    continue
                }

                do {
                    _ = try await api.runStoreAutomationJob(job.name)
                    defaults.set(key, forKey: lastRunPrefix + job.name)
                } catch {
                    // Leave the job eligible so a later scheduler pass can retry.
                }
            }
        } catch {
            // The bundled backend may still be starting or Plex may be unavailable.
            // The next scheduler pass will retry without surfacing repeated UI errors.
        }
    }

    private func isDue(
        _ job: StoreAutomationJob,
        at date: Date,
        calendar: Calendar
    ) -> Bool {
        let components = calendar.dateComponents(
            [.month, .weekday, .hour, .minute],
            from: date
        )

        if let month = job.calendar.month,
           components.month != month {
            return false
        }

        if let weekday = job.calendar.weekday,
           components.weekday != weekday {
            return false
        }

        guard let hour = components.hour,
              let minute = components.minute else {
            return false
        }

        if hour > job.calendar.hour {
            return true
        }

        return hour == job.calendar.hour && minute >= job.calendar.minute
    }

    private func runKey(
        for job: StoreAutomationJob,
        at date: Date,
        calendar: Calendar
    ) -> String {
        let parts = calendar.dateComponents([.year, .month, .day], from: date)
        let year = parts.year ?? 0
        let month = parts.month ?? 0
        let day = parts.day ?? 0
        return String(format: "%04d-%02d-%02d", year, month, day)
    }
}
