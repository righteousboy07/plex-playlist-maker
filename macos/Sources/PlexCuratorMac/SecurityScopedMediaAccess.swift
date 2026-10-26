import Foundation

@MainActor
final class SecurityScopedMediaAccess {
    static let shared = SecurityScopedMediaAccess()

    private struct StoredBookmark: Codable {
        let path: String
        let bookmark: Data
    }

    private let defaultsKey = "plexCurator.mediaOrganizer.securityScopedBookmarks"
    private var activeURLs: [String: URL] = [:]
    private var didRestore = false

    private init() {}

    func restoreAccess() {
        guard BuildFlavor.current.isAppStore, !didRestore else { return }
        didRestore = true

        var refreshed: [StoredBookmark] = []

        for stored in loadStoredBookmarks() {
            var stale = false

            do {
                let url = try URL(
                    resolvingBookmarkData: stored.bookmark,
                    options: [.withSecurityScope],
                    relativeTo: nil,
                    bookmarkDataIsStale: &stale
                )

                guard url.startAccessingSecurityScopedResource() else {
                    continue
                }

                let key = normalizedPath(url.path)
                activeURLs[key] = url

                if stale {
                    let updated = try url.bookmarkData(
                        options: [.withSecurityScope],
                        includingResourceValuesForKeys: nil,
                        relativeTo: nil
                    )
                    refreshed.append(StoredBookmark(path: key, bookmark: updated))
                } else {
                    refreshed.append(StoredBookmark(path: key, bookmark: stored.bookmark))
                }
            } catch {
                continue
            }
        }

        saveStoredBookmarks(refreshed)
    }

    @discardableResult
    func authorize(_ url: URL) throws -> String {
        guard BuildFlavor.current.isAppStore else {
            return normalizedPath(url.path)
        }

        restoreAccess()

        let bookmark = try url.bookmarkData(
            options: [.withSecurityScope],
            includingResourceValuesForKeys: nil,
            relativeTo: nil
        )

        guard url.startAccessingSecurityScopedResource() else {
            throw SecurityScopedMediaAccessError.accessDenied(url.path)
        }

        let path = normalizedPath(url.path)

        if let existing = activeURLs[path], existing != url {
            existing.stopAccessingSecurityScopedResource()
        }
        activeURLs[path] = url

        var stored = loadStoredBookmarks().filter {
            normalizedPath($0.path) != path
        }
        stored.append(StoredBookmark(path: path, bookmark: bookmark))
        saveStoredBookmarks(stored)

        return path
    }

    func isAuthorized(path: String) -> Bool {
        guard BuildFlavor.current.isAppStore else { return true }
        restoreAccess()

        let candidate = normalizedPath(path)
        return activeURLs.keys.contains { root in
            candidate == root || candidate.hasPrefix(root + "/")
        }
    }

    func stopAll() {
        for url in activeURLs.values {
            url.stopAccessingSecurityScopedResource()
        }
        activeURLs.removeAll()
        didRestore = false
    }

    private func loadStoredBookmarks() -> [StoredBookmark] {
        guard let data = UserDefaults.standard.data(forKey: defaultsKey) else {
            return []
        }

        return (try? PropertyListDecoder().decode([StoredBookmark].self, from: data)) ?? []
    }

    private func saveStoredBookmarks(_ bookmarks: [StoredBookmark]) {
        guard let data = try? PropertyListEncoder().encode(bookmarks) else { return }
        UserDefaults.standard.set(data, forKey: defaultsKey)
    }

    private func normalizedPath(_ path: String) -> String {
        URL(fileURLWithPath: path)
            .standardizedFileURL
            .resolvingSymlinksInPath()
            .path
    }
}

enum SecurityScopedMediaAccessError: LocalizedError {
    case accessDenied(String)

    var errorDescription: String? {
        switch self {
        case .accessDenied(let path):
            return "Plex Curator could not retain access to the selected folder: \(path)"
        }
    }
}
