import Foundation

@MainActor
final class StoreAutomationScheduler: ObservableObject {
    static let shared = StoreAutomationScheduler()

    @Published private(set) var jobs: [StoreAutomationJob] = []
    @Published private(set) var runningJob: String?
    @Published private(set) var lastSchedulerError: String?

    private var task: Task<Void, Never>?
    private let defaults = UserDefaults.standard
    private let lastRunPrefix = "plexCurator.storeAutomation.lastRun."

    private init() {}

    func start(api: APIClient) {
        guard BuildFlavor.current.isAppStore else { return }
        guard task == nil else { return }

        task = Task { [weak self] in
            guard let self else { return }

            await self.reload(api: api)

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
        runningJob = nil
    }

    func reload(api: APIClient) async {
        guard BuildFlavor.current.isAppStore else { return }

        do {
            jobs = try await api.storeAutomationJobs()
            lastSchedulerError = nil
        } catch {
            lastSchedulerError = error.localizedDescription
        }
    }

    func runNow(_ job: StoreAutomationJob, api: APIClient) async -> Bool {
        guard BuildFlavor.current.isAppStore else { return false }
        guard runningJob == nil else { return false }

        runningJob = job.name
        defer { runningJob = nil }

        do {
            _ = try await api.runStoreAutomationJob(job.name)
            defaults.set(
                runKey(for: job, at: Date(), calendar: Calendar.current),
                forKey: lastRunPrefix + job.name
            )
            lastSchedulerError = nil
            return true
        } catch {
            lastSchedulerError = error.localizedDescription
            return false
        }
    }

    func lastRunText(for job: StoreAutomationJob) -> String {
        guard let raw = defaults.string(forKey: lastRunPrefix + job.name) else {
            return "Never"
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"

        if let date = formatter.date(from: raw) {
            formatter.dateStyle = .medium
            formatter.timeStyle = .none
            return formatter.string(from: date)
        }

        return raw
    }

    func scheduleText(for job: StoreAutomationJob) -> String {
        var pieces: [String] = []

        if let month = job.calendar.month {
            let symbols = Calendar.current.monthSymbols
            if (1...symbols.count).contains(month) {
                pieces.append(symbols[month - 1])
            }
        }

        if let weekday = job.calendar.weekday {
            let symbols = Calendar.current.weekdaySymbols
            if (1...symbols.count).contains(weekday) {
                pieces.append(symbols[weekday - 1])
            }
        }

        let time = Calendar.current.date(
            from: DateComponents(hour: job.calendar.hour, minute: job.calendar.minute)
        )
        if let time {
            let formatter = DateFormatter()
            formatter.timeStyle = .short
            pieces.append(formatter.string(from: time))
        }

        return pieces.isEmpty ? "Scheduled" : pieces.joined(separator: " • ")
    }

    private func runDueJobs(api: APIClient) async {
        StoreAutomationManager.shared.refresh()
        guard StoreAutomationManager.shared.enabled else { return }

        do {
            if jobs.isEmpty {
                jobs = try await api.storeAutomationJobs()
            }

            let now = Date()
            let calendar = Calendar.current

            for job in jobs where isDue(job, at: now, calendar: calendar) {
                let key = runKey(for: job, at: now, calendar: calendar)
                guard defaults.string(forKey: lastRunPrefix + job.name) != key else {
                    continue
                }

                runningJob = job.name
                do {
                    _ = try await api.runStoreAutomationJob(job.name)
                    defaults.set(key, forKey: lastRunPrefix + job.name)
                    lastSchedulerError = nil
                } catch {
                    lastSchedulerError = error.localizedDescription
                }
                runningJob = nil
            }
        } catch {
            lastSchedulerError = error.localizedDescription
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
