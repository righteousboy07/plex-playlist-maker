import AppKit
import Foundation

enum PlexCuratorRuntimePaths {
    static var appStoreSupportDirectory: URL {
        let base = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first!
        return base.appendingPathComponent("Plex Curator", isDirectory: true)
    }

    static var appStoreLogDirectory: URL {
        let library = FileManager.default.urls(
            for: .libraryDirectory,
            in: .userDomainMask
        ).first!
        return library
            .appendingPathComponent("Logs", isDirectory: true)
            .appendingPathComponent("PlexCurator", isDirectory: true)
    }

    static var apiKeyURL: URL {
        if BuildFlavor.current.isAppStore {
            return appStoreSupportDirectory.appendingPathComponent("api.key")
        }

        return FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".config/plex-curator/api.key")
    }
}

enum AppStoreBackendRuntimeError: LocalizedError {
    case missingHelper(String)
    case launchFailed(String)
    case startupTimedOut

    var errorDescription: String? {
        switch self {
        case .missingHelper(let path):
            return "The bundled Plex Curator backend is missing at \(path)."
        case .launchFailed(let message):
            return "The bundled Plex Curator backend could not start: \(message)"
        case .startupTimedOut:
            return "The bundled Plex Curator backend did not become ready in time."
        }
    }
}

@MainActor
final class AppStoreBackendRuntime {
    static let shared = AppStoreBackendRuntime()

    private var process: Process?

    private init() {}

    func ensureRunning() async throws {
        guard BuildFlavor.current.isAppStore else { return }

        if await ping() {
            return
        }

        if process?.isRunning != true {
            try launch()
        }

        for _ in 0..<30 {
            if await ping() {
                return
            }
            try await Task.sleep(nanoseconds: 250_000_000)
        }

        throw AppStoreBackendRuntimeError.startupTimedOut
    }

    func stop() {
        guard BuildFlavor.current.isAppStore else { return }
        if process?.isRunning == true {
            process?.terminate()
        }
        process = nil
    }

    func reloadMediaFolderAccess() async throws {
        guard BuildFlavor.current.isAppStore else { return }
        stop()
        try await Task.sleep(nanoseconds: 150_000_000)
        try await ensureRunning()
    }

    private func launch() throws {
        SecurityScopedMediaAccess.shared.restoreAccess()
        let helpers = Bundle.main.bundleURL
            .appendingPathComponent("Contents", isDirectory: true)
            .appendingPathComponent("Helpers", isDirectory: true)
        let helperApp = helpers
            .appendingPathComponent("PlexCuratorBackend.app", isDirectory: true)
        let executable = helperApp
            .appendingPathComponent("Contents", isDirectory: true)
            .appendingPathComponent("MacOS", isDirectory: true)
            .appendingPathComponent("plex-curator-api")
        let examples = helperApp
            .appendingPathComponent("Contents", isDirectory: true)
            .appendingPathComponent("Resources", isDirectory: true)
            .appendingPathComponent("examples", isDirectory: true)

        guard FileManager.default.isExecutableFile(atPath: executable.path) else {
            throw AppStoreBackendRuntimeError.missingHelper(executable.path)
        }

        do {
            try FileManager.default.createDirectory(
                at: PlexCuratorRuntimePaths.appStoreSupportDirectory,
                withIntermediateDirectories: true
            )
            try FileManager.default.createDirectory(
                at: PlexCuratorRuntimePaths.appStoreLogDirectory,
                withIntermediateDirectories: true
            )
        } catch {
            throw AppStoreBackendRuntimeError.launchFailed(error.localizedDescription)
        }

        var environment = ProcessInfo.processInfo.environment
        environment["PLEX_CURATOR_DISTRIBUTION"] = "app-store"
        environment["PLEX_CURATOR_CONFIG_DIR"] =
            PlexCuratorRuntimePaths.appStoreSupportDirectory.path
        environment["PLEX_CURATOR_LOG_DIR"] =
            PlexCuratorRuntimePaths.appStoreLogDirectory.path
        environment["PLEX_CURATOR_EXAMPLES_DIR"] = examples.path

        let process = Process()
        process.executableURL = executable
        process.arguments = [
            "serve",
            "--port",
            "\(BuildFlavor.current.apiPort)",
            "--no-access-log"
        ]
        process.environment = environment
        process.currentDirectoryURL = executable.deletingLastPathComponent()
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            self.process = process
        } catch {
            throw AppStoreBackendRuntimeError.launchFailed(error.localizedDescription)
        }
    }

    private func ping() async -> Bool {
        var request = URLRequest(
            url: URL(
                string: "\(BuildFlavor.current.apiAddress)/api/v1/ping"
            )!
        )
        request.timeoutInterval = 1

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else { return false }
            return http.statusCode == 200
        } catch {
            return false
        }
    }
}

@MainActor
final class PlexCuratorApplicationDelegate: NSObject, NSApplicationDelegate {
    func applicationWillTerminate(_ notification: Notification) {
        StoreAutomationScheduler.shared.stop()
        AppStoreBackendRuntime.shared.stop()
        SecurityScopedMediaAccess.shared.stopAll()
    }
}
