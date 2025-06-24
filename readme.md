# Zmito's Minecraft Versions API

This API provides endpoints to retrieve various versions related to Minecraft, including base game versions, and versions for popular mod loaders like Fabric, Quilt, Forge, and NeoForge.

## Base URL

`http://127.0.0.1:8000`

## 1. Get Minecraft Versions

Retrieves the list of Minecraft versions. Can be filtered by 'release' or 'snapshot' type.

### Endpoint

`GET /mc/versions`

### Query Parameters

| **Name** | **Type** | **Description** | **Default** |
| :---------- | :------ | :-------------------------------------------------------------------------- | :------ |
| `version_type` | `string` | Optional filter for version type: `'release'` or `'snapshot'`. If not provided, all versions are returned. | `None` |

### Example Usage

* **Get all Minecraft versions:** `GET /mc/versions`

* **Get only release Minecraft versions:** `GET /mc/versions?version_type=release`

* **Get only snapshot Minecraft versions:** `GET /mc/versions?version_type=snapshot`

## 2. Get Fabric Loader Versions

Retrieves the list of available Fabric Loader versions for a specific Minecraft version or the latest release.

### Endpoint

`GET /mc/loaders/fabric`

### Query Parameters

| **Name** | **Type** | **Description** | **Default** |
| :----------------- | :------ | :------------------------------------------------------------------------------------------------------ | :------ |
| `minecraft_version` | `string` | Optional Minecraft version (e.g., `'1.18.2'`, `'1.20.1'`). If not provided, uses the latest Minecraft release version. | `None` |

### Example Usage

* **Get Fabric versions for the latest Minecraft release:** `GET /mc/loaders/fabric`

* **Get Fabric versions for Minecraft 1.20.1:** `GET /mc/loaders/fabric?minecraft_version=1.20.1`

## 3. Get Stable Quilt Loader Versions

Retrieves the list of stable Quilt Loader versions (excluding betas and pre-releases).

### Endpoint

`GET /mc/loaders/quilt`

### Query Parameters

* None

### Example Usage

* **Get stable Quilt versions:** `GET /mc/loaders/quilt`

## 4. Get Forge Versions

Retrieves the list of available Forge versions that match a specific Minecraft version or the latest release. Can return only the build version.

### Endpoint

`GET /mc/loaders/forge`

### Query Parameters

| **Name** | **Type** | **Description** | **Default** |
| :----------------- | :-------- | :------------------------------------------------------------------------------------------------------ | :------ |
| `minecraft_version` | `string` | Optional Minecraft version (e.g., `'1.18.2'`, `'1.20.1'`). If not provided, uses the latest Minecraft release version. | `None` |
| `version_only` | `boolean` | If `true`, returns only the Forge build version (e.g., `'56.0.8'` instead of `'1.21.6-56.0.8'`). | `false` |

### Example Usage

* **Get Forge versions for the latest Minecraft release:** `GET /mc/loaders/forge`

* **Get Forge versions for Minecraft 1.21.6:** `GET /mc/loaders/forge?minecraft_version=1.21.6`

* **Get only the build numbers for Forge versions for Minecraft 1.21.6:** `GET /mc/loaders/forge?minecraft_version=1.21.6&version_only=true`

## 5. Get NeoForge Versions

Retrieves the list of NeoForge versions for a specific Minecraft version or the latest release. Can filter by 'release' type to exclude betas.

### Endpoint

`GET /mc/loaders/neoforge`

### Query Parameters

| **Name** | **Type** | **Description** | **Default** |
| :----------------- | :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :------ |
| `minecraft_version` | `string` | Optional Minecraft version. If not provided, uses the latest Minecraft release version. Note: This parameter is primarily for consistency, the NeoForge API does not always filter by MC version directly in its metadata. | `None` |
| `version_type` | `string` | Optional filter for NeoForge version type: `'release'` to exclude beta versions. If not provided, all versions are returned. | `None` |

### Example Usage

* **Get all NeoForge versions (latest first):**
    `GET /mc/loaders/neoforge`

* **Get only stable (non-beta) NeoForge versions:**
    `GET /mc/loaders/neoforge?version_type=release`

* **Get all NeoForge versions, passing a Minecraft version (which won't filter results for NeoForge specifically, but is there for consistency):**
    `GET /mc/loaders/neoforge?minecraft_version=1.20.1`