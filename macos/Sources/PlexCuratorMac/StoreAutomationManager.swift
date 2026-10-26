import Foundation
import ServiceManagement

@MainActor
final class StoreAutomationManager: ObservableObject {
    static let shared = StoreAutomationManager()

    @Published private(set) var statusText = "Checking…"
    @Published private(set) var enabled = false
    @Published private(set) var requiresApproval = false
    @Published private(set) var lastError: String?

    private init() {}

    func refresh() {
        guard BuildFlavor.current.isAppStore else {
            enabled = false
            requiresApproval = false
            statusText = "Direct edition uses LaunchAgents."
            lastError = nil
            return
        }

        guard #available(macOS 13.0, *) else {
            enabled = false
            requiresApproval = false
            statusText = "Requires macOS 13 or newer."
            return
        }

        let status = SMAppService.mainApp.status
        enabled = status == .enabled
        requiresApproval = status == .requiresApproval

        switch status {
        case .enabled:
            statusText = "Enabled"
        case .requiresApproval:
            statusText = "Needs approval in Login Items"
        case .notRegistered:
            statusText = "Disabled"
        case .notFound:
            statusText = "Unavailable in this build"
        @unknown default:
            statusText = "Unknown"
        }
    }

    func setEnabled(_ shouldEnable: Bool) async {
        guard BuildFlavor.current.isAppStore else { return }

        guard #available(macOS 13.0, *) else {
            lastError = "Store background automation requires macOS 13 or newer."
            refresh()
            return
        }

        do {
            if shouldEnable {
                if SMAppService.mainApp.status != .enabled {
                    try SMAppService.mainApp.register()
                }
            } else if SMAppService.mainApp.status != .notRegistered {
                try await SMAppService.mainApp.unregister()
            }
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }

        refresh()
    }

    func openLoginItemsSettings() {
        guard BuildFlavor.current.isAppStore else { return }
        guard #available(macOS 13.0, *) else { return }
        SMAppService.openSystemSettingsLoginItems()
    }
}
