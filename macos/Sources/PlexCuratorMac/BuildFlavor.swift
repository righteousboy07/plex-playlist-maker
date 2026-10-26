import Foundation

enum DistributionChannel: String {
    case direct
    case appStore
}

struct BuildFlavor {
    let channel: DistributionChannel
    let displayName: String
    let supportsExternalInstaller: Bool
    let supportsLaunchAgentManagement: Bool
    let supportsExternalLogFiles: Bool
    let usesAppSandbox: Bool

    static let current: BuildFlavor = {
#if APP_STORE
        return BuildFlavor(
            channel: .appStore,
            displayName: "Mac App Store",
            supportsExternalInstaller: false,
            supportsLaunchAgentManagement: false,
            supportsExternalLogFiles: false,
            usesAppSandbox: true
        )
#else
        return BuildFlavor(
            channel: .direct,
            displayName: "Direct Download",
            supportsExternalInstaller: true,
            supportsLaunchAgentManagement: true,
            supportsExternalLogFiles: true,
            usesAppSandbox: false
        )
#endif
    }()

    var isAppStore: Bool {
        channel == .appStore
    }

    var onboardingDescription: String {
        switch channel {
        case .direct:
            return "The installer has already set up the local API, background service, automation manager, and 30-day log retention. The only thing left is connecting Plex Curator to your Plex server."
        case .appStore:
            return "This Mac App Store build keeps all components inside the app sandbox. Connect Plex Curator to your Plex server to finish setup."
        }
    }

    var automationUnavailableMessage: String {
        "The Mac App Store edition does not install external LaunchAgents. Background services for this edition will use Apple-approved bundled service APIs."
    }
}
