import SwiftUI
import Foundation

// MARK: - API Models

struct LibraryInfo: Codable, Identifiable {
    var id: String { "\(name)-\(type)" }
    let name: String
    let type: String
}

struct PlexStatus: Codable {
    let connected: Bool
    let serverName: String?
    let serverVersion: String?
    let libraries: [LibraryInfo]
    let error: String?
}

struct StatusResponse: Codable {
    let apiVersion: String
    let curatorVersion: String
    let plex: PlexStatus
    let stationCount: Int
    let enabledStationCount: Int
}

struct Station: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String?
    let enabled: Bool
    let playlist: String
    let preset: String
    let yearMin: Int?
    let yearMax: Int?
    let kidsOnly: Bool
    let adult: Bool
    let perShow: Int
    let total: Int
    let avoidRecent: Int
    let minShowGap: Int
    let seasonal: String
    let specialEvery: Int
    let unwatched: Bool
    let syncWatchProgress: Bool
    let includeShows: [String]
    let excludeShows: [String]
}

struct StationsResponse: Codable { let stations: [Station] }

struct MediaItem: Codable, Identifiable {
    var id: String { ratingKey.isEmpty ? "\(position ?? 0)-\(title ?? "")" : ratingKey }
    let ratingKey: String
    let type: String?
    let title: String?
    let year: Int?
    let watched: Bool
    let position: Int?
    let showTitle: String?
    let seasonNumber: Int?
    let episodeNumber: Int?

    var displayTitle: String {
        if type == "episode" {
            return "\(showTitle ?? "Unknown") — S\(String(format: "%02d", seasonNumber ?? 0))E\(String(format: "%02d", episodeNumber ?? 0)) — \(title ?? "")"
        }
        return year.map { "\(title ?? "Untitled") (\($0))" } ?? (title ?? "Untitled")
    }
}

struct PreviewResponse: Codable {
    let station: Station
    let showCount: Int
    let seasonalMode: String
    let itemCount: Int
    let items: [MediaItem]
}

struct StationDiff: Codable {
    let currentCount: Int
    let proposedCount: Int
    let keepCount: Int
    let addCount: Int
    let removeCount: Int
    let movedCount: Int
    let added: [String]
    let removed: [String]
}

struct DiffResponse: Codable {
    let station: Station
    let diff: StationDiff
}

struct DoctorCheck: Codable, Identifiable {
    var id: String { "\(status)-\(label)-\(detail)" }
    let status: String
    let label: String
    let detail: String
}

struct DoctorResponse: Codable {
    let result: String
    let failures: Int
    let warnings: Int
    let checks: [DoctorCheck]
}

struct HistoryItem: Codable, Identifiable {
    var id: String { "\(selectedAt)-\(channelName)-\(showTitle)-\(seasonNumber)-\(episodeNumber)" }
    let selectedAt: String
    let showTitle: String
    let seasonNumber: Int
    let episodeNumber: Int
    let episodeTitle: String
    let channelName: String
}

struct HistoryResponse: Codable { let history: [HistoryItem] }

struct LogResponse: Codable {
    let job: String
    let errors: Bool
    let path: String
    let lines: [String]
}

struct APIErrorResponse: Codable { let detail: String }
struct PreviewRequest: Codable { let total: Int? }
struct RefreshRequest: Codable { let total: Int?; let dryRun: Bool; let force: Bool }

struct RefreshResponse: Codable {
    let ok: Bool
    let dryRun: Bool
    let stationId: String?
    let playlist: String?
    let itemCount: Int?
}

// MARK: - API Client

enum APIClientError: LocalizedError {
    case missingKey(String)
    case server(Int, String)
    case invalidResponse
    case transport(String)

    var errorDescription: String? {
        switch self {
        case .missingKey(let path): return "API key missing at \(path). Start the v12 API once or run ./plex-curator-api key."
        case .server(let code, let message): return "API \(code): \(message)"
        case .invalidResponse: return "Invalid API response."
        case .transport(let message): return message
        }
    }
}

final class APIClient {
    let baseURL = URL(string: "http://127.0.0.1:8765")!

    private var decoder: JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }

    private var encoder: JSONEncoder {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }

    var apiKeyPath: String {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".config/plex-curator/api.key").path
    }

    private func apiKey() throws -> String {
        guard let key = try? String(contentsOfFile: apiKeyPath, encoding: .utf8)
            .trimmingCharacters(in: .whitespacesAndNewlines), !key.isEmpty else {
            throw APIClientError.missingKey(apiKeyPath)
        }
        return key
    }

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        body: Data? = nil,
        authenticated: Bool = false
    ) async throws -> T {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIClientError.invalidResponse
        }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.timeoutInterval = 30
        req.setValue("application/json", forHTTPHeaderField: "Accept")
        if let body {
            req.httpBody = body
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if authenticated {
            req.setValue(try apiKey(), forHTTPHeaderField: "X-Plex-Curator-Key")
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: req)
            guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }
            guard (200..<300).contains(http.statusCode) else {
                let detail = (try? decoder.decode(APIErrorResponse.self, from: data).detail)
                    ?? String(data: data, encoding: .utf8) ?? "Unknown error"
                throw APIClientError.server(http.statusCode, detail)
            }
            return try decoder.decode(T.self, from: data)
        } catch let e as APIClientError {
            throw e
        } catch {
            throw APIClientError.transport(error.localizedDescription)
        }
    }

    func status() async throws -> StatusResponse {
        try await request("/api/v1/status")
    }

    func stations() async throws -> [Station] {
        let r: StationsResponse = try await request("/api/v1/stations")
        return r.stations
    }

    func doctor() async throws -> DoctorResponse {
        try await request("/api/v1/doctor")
    }

    func preview(_ id: String) async throws -> PreviewResponse {
        let body = try encoder.encode(PreviewRequest(total: nil))
        return try await request("/api/v1/stations/\(id)/preview", method: "POST", body: body)
    }

    func diff(_ id: String) async throws -> DiffResponse {
        try await request("/api/v1/stations/\(id)/diff")
    }

    func refresh(_ id: String, dryRun: Bool) async throws -> RefreshResponse {
        let body = try encoder.encode(RefreshRequest(total: nil, dryRun: dryRun, force: false))
        return try await request(
            "/api/v1/stations/\(id)/refresh",
            method: "POST",
            body: body,
            authenticated: true
        )
    }

    func history() async throws -> [HistoryItem] {
        let r: HistoryResponse = try await request("/api/v1/history?limit=150")
        return r.history
    }

    func logs(job: String, errors: Bool) async throws -> LogResponse {
        let escaped = job.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? job
        return try await request("/api/v1/logs/\(escaped)?errors=\(errors ? "true" : "false")&lines=250")
    }
}

// MARK: - App Model

@MainActor
final class AppModel: ObservableObject {
    @Published var status: StatusResponse?
    @Published var stations: [Station] = []
    @Published var doctor: DoctorResponse?
    @Published var history: [HistoryItem] = []
    @Published var preview: PreviewResponse?
    @Published var diff: DiffResponse?
    @Published var log: LogResponse?
    @Published var error: String?
    @Published var message: String?
    @Published var loading = false

    let api = APIClient()

    func bootstrap() async { await refreshDashboard() }

    func refreshDashboard() async {
        loading = true
        defer { loading = false }
        do {
            async let s = api.status()
            async let st = api.stations()
            async let d = api.doctor()
            status = try await s
            stations = try await st
            doctor = try await d
            error = nil
        } catch {
            status = nil
            self.error = error.localizedDescription
        }
    }

    func loadPreview(_ station: Station) async {
        do { preview = try await api.preview(station.id); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func loadDiff(_ station: Station) async {
        do { diff = try await api.diff(station.id); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func dryRun(_ station: Station) async {
        do {
            _ = try await api.refresh(station.id, dryRun: true)
            message = "Dry run completed. No Plex changes were made."
            diff = try await api.diff(station.id)
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    func refresh(_ station: Station) async {
        do {
            let r = try await api.refresh(station.id, dryRun: false)
            message = "Refreshed \(r.playlist ?? station.name) with \(r.itemCount ?? 0) items."
            preview = nil
            diff = nil
            await refreshDashboard()
        } catch { self.error = error.localizedDescription }
    }

    func loadHistory() async {
        do { history = try await api.history(); error = nil }
        catch { self.error = error.localizedDescription }
    }

    func loadLogs(job: String, errors: Bool) async {
        do { log = try await api.logs(job: job, errors: errors); error = nil }
        catch { self.error = error.localizedDescription }
    }
}

// MARK: - App

@main
struct PlexCuratorMacApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup("Plex Curator") {
            RootView()
                .environmentObject(model)
                .frame(minWidth: 980, minHeight: 650)
                .task { await model.bootstrap() }
        }
    }
}

// MARK: - Views

struct RootView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationView {
            List {
                Section("Plex Curator") {
                    NavigationLink(destination: DashboardView()) { Label("Dashboard", systemImage: "gauge") }
                    NavigationLink(destination: StationsView()) { Label("Stations", systemImage: "tv") }
                    NavigationLink(destination: HistoryView()) { Label("History", systemImage: "clock.arrow.circlepath") }
                    NavigationLink(destination: HealthView()) { Label("Health", systemImage: "heart.text.square") }
                    NavigationLink(destination: LogsView()) { Label("Logs", systemImage: "doc.text.magnifyingglass") }
                    NavigationLink(destination: SettingsView()) { Label("Settings", systemImage: "gearshape") }
                }
            }
            .listStyle(SidebarListStyle())
            .frame(minWidth: 210)

            DashboardView()
        }
        .overlay(alignment: .bottom) {
            if let error = model.error {
                notice(icon: "exclamationmark.triangle.fill", text: error) { model.error = nil }
            } else if let message = model.message {
                notice(icon: "checkmark.circle.fill", text: message) { model.message = nil }
            }
        }
    }

    private func notice(icon: String, text: String, dismiss: @escaping () -> Void) -> some View {
        HStack {
            Image(systemName: icon)
            Text(text).lineLimit(2)
            Spacer()
            Button("Dismiss", action: dismiss)
        }
        .padding(10)
        .background(.ultraThickMaterial)
    }
}

struct StatusBadge: View {
    let text: String
    let good: Bool
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(good ? Color.green : Color.orange).frame(width: 8, height: 8)
            Text(text).font(.caption)
        }
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(Color.secondary.opacity(0.12)).clipShape(Capsule())
    }
}

struct DashboardView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Plex Curator").font(.largeTitle.bold())
                        Text("Local programming control").foregroundColor(.secondary)
                    }
                    Spacer()
                    StatusBadge(
                        text: model.status?.plex.connected == true ? "Plex Connected" : "Offline",
                        good: model.status?.plex.connected == true
                    )
                    Button("Refresh") { Task { await model.refreshDashboard() } }
                }

                if let s = model.status {
                    infoBox("Plex Server", "\(s.plex.serverName ?? "Unknown") \(s.plex.serverVersion ?? "")")
                    infoBox("Stations", "\(s.enabledStationCount) enabled / \(s.stationCount) configured")
                    infoBox("Versions", "Curator \(s.curatorVersion) • API \(s.apiVersion)")
                    infoBox("Health", model.doctor?.result ?? "Unknown")

                    GroupBox("Libraries") {
                        VStack(alignment: .leading, spacing: 7) {
                            ForEach(s.plex.libraries) { lib in
                                HStack {
                                    Image(systemName: lib.type == "movie" ? "film" : "tv")
                                    Text(lib.name)
                                    Spacer()
                                    Text(lib.type).foregroundColor(.secondary)
                                }
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                } else {
                    GroupBox("API unavailable") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Start the local backend API:")
                            Text("./plex-curator-api serve").font(.system(.body, design: .monospaced))
                            Text("or install the api-server LaunchAgent.").foregroundColor(.secondary)
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }.padding(24)
        }.navigationTitle("Dashboard")
    }

    private func infoBox(_ title: String, _ value: String) -> some View {
        GroupBox(title) {
            Text(value).font(.title3.bold()).frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct StationsView: View {
    @EnvironmentObject var model: AppModel
    var body: some View {
        List(model.stations) { station in
            NavigationLink(destination: StationDetailView(station: station)) {
                HStack {
                    Image(systemName: station.enabled ? "play.tv.fill" : "pause.tv")
                    VStack(alignment: .leading) {
                        Text(station.name).font(.headline)
                        Text(station.description ?? station.playlist)
                            .font(.caption).foregroundColor(.secondary).lineLimit(1)
                    }
                    Spacer()
                    Text("\(station.total) items").foregroundColor(.secondary)
                }.padding(.vertical, 3)
            }
        }.navigationTitle("Stations")
    }
}

struct StationDetailView: View {
    @EnvironmentObject var model: AppModel
    let station: Station
    @State private var tab = 0
    @State private var confirmRefresh = false

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(station.name).font(.title.bold())
                    Text(station.playlist).foregroundColor(.secondary)
                }
                Spacer()
                Button("Preview") { tab = 1; Task { await model.loadPreview(station) } }
                Button("Diff") { tab = 2; Task { await model.loadDiff(station) } }
                Button("Dry Run") { Task { await model.dryRun(station) } }
                Button("Refresh") { confirmRefresh = true }.disabled(!station.enabled)
            }.padding()

            Picker("", selection: $tab) {
                Text("Overview").tag(0); Text("Preview").tag(1); Text("Diff").tag(2)
            }.pickerStyle(SegmentedPickerStyle()).padding(.horizontal)

            Divider().padding(.top, 10)

            if tab == 0 { overview }
            else if tab == 1 { previewList }
            else { diffView }
        }
        .navigationTitle(station.name)
        .alert(isPresented: $confirmRefresh) {
            Alert(
                title: Text("Refresh \(station.name)?"),
                message: Text("This replaces the station's current Plex playlist."),
                primaryButton: .destructive(Text("Refresh")) { Task { await model.refresh(station) } },
                secondaryButton: .cancel()
            )
        }
    }

    private var overview: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                row("Enabled", station.enabled ? "Yes" : "No")
                row("Preset", station.preset)
                row("Total", "\(station.total)")
                row("Per show", "\(station.perShow)")
                row("Show gap", "\(station.minShowGap)")
                row("Avoid recent", "\(station.avoidRecent)")
                row("Seasonal", station.seasonal)
                row("Watch progress", station.syncWatchProgress ? "Follow Plex" : "Independent")
                row("Years", "\(station.yearMin.map(String.init) ?? "…")–\(station.yearMax.map(String.init) ?? "…")")
                row("Included shows", station.includeShows.isEmpty ? "All qualifying" : station.includeShows.joined(separator: ", "))
                row("Excluded shows", station.excludeShows.isEmpty ? "None" : station.excludeShows.joined(separator: ", "))
            }.padding(22)
        }
    }

    private func row(_ name: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(name).foregroundColor(.secondary).frame(width: 130, alignment: .leading)
            Text(value)
            Spacer()
        }
    }

    private var previewList: some View {
        Group {
            if let p = model.preview, p.station.id == station.id {
                List(p.items) { item in Text(item.displayTitle) }
            } else {
                Button("Load Preview") { Task { await model.loadPreview(station) } }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private var diffView: some View {
        Group {
            if let d = model.diff, d.station.id == station.id {
                VStack {
                    HStack(spacing: 25) {
                        metric("KEEP", d.diff.keepCount)
                        metric("ADD", d.diff.addCount)
                        metric("REMOVE", d.diff.removeCount)
                        metric("MOVED", d.diff.movedCount)
                        Spacer()
                    }.padding()

                    HSplitView {
                        List(d.diff.added, id: \.self) { Label($0, systemImage: "plus.circle") }
                        List(d.diff.removed, id: \.self) { Label($0, systemImage: "minus.circle") }
                    }
                }
            } else {
                Button("Load Diff") { Task { await model.loadDiff(station) } }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func metric(_ name: String, _ value: Int) -> some View {
        VStack { Text("\(value)").font(.title2.bold()); Text(name).font(.caption).foregroundColor(.secondary) }
    }
}

struct HistoryView: View {
    @EnvironmentObject var model: AppModel
    var body: some View {
        List(model.history) { item in
            VStack(alignment: .leading) {
                Text("\(item.showTitle) S\(String(format: "%02d", item.seasonNumber))E\(String(format: "%02d", item.episodeNumber)) — \(item.episodeTitle)")
                Text(item.channelName).font(.caption).foregroundColor(.secondary)
            }.padding(.vertical, 3)
        }
        .navigationTitle("History")
        .task { await model.loadHistory() }
    }
}

struct HealthView: View {
    @EnvironmentObject var model: AppModel
    var body: some View {
        List(model.doctor?.checks ?? []) { check in
            HStack(alignment: .top) {
                Image(systemName: check.status == "PASS" ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                    .foregroundColor(check.status == "PASS" ? .green : .orange)
                VStack(alignment: .leading) {
                    Text(check.label)
                    Text(check.detail).font(.caption).foregroundColor(.secondary)
                }
            }
        }.navigationTitle("Health")
    }
}

struct LogsView: View {
    @EnvironmentObject var model: AppModel
    @State private var job = "api-server"
    @State private var errors = false

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                TextField("Job", text: $job).textFieldStyle(RoundedBorderTextFieldStyle()).frame(width: 220)
                Toggle("Errors", isOn: $errors)
                Button("Load") { Task { await model.loadLogs(job: job, errors: errors) } }
                Spacer()
            }.padding()
            Divider()
            ScrollView([.vertical, .horizontal]) {
                Text(model.log?.lines.joined(separator: "\n") ?? "No log loaded.")
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                    .padding()
            }
        }.navigationTitle("Logs")
    }
}

struct SettingsView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Local API").font(.title2.bold())
            setting("Address", "http://127.0.0.1:8765")
            setting("API key", model.api.apiKeyPath)
            setting("Exposure", "localhost only")
            setting("CORS", "disabled")
            Divider()
            Text("Backend").font(.title2.bold())
            setting("Curator", model.status.map { "v\($0.curatorVersion)" } ?? "Unavailable")
            setting("API", model.status.map { "v\($0.apiVersion)" } ?? "Unavailable")
            Spacer()
        }.padding(24).navigationTitle("Settings")
    }

    private func setting(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(label).foregroundColor(.secondary).frame(width: 100, alignment: .leading)
            Text(value).textSelection(.enabled)
            Spacer()
        }
    }
}