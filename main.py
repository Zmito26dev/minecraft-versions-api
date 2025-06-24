import httpx
from fastapi import FastAPI, HTTPException, Path, Query
from typing import List, Optional
import xml.etree.ElementTree as ET
import re
import time

app = FastAPI(
  title="Zmito's Minecraft Versions API",
  description="API to get versions for Minecraft base, snapshots, Forge, NeoForge, Fabric, and Quilt.",
  version="1.0.0"
)

# Initialize HTTPX client for making requests
# Using async client for better performance in FastAPI
http_client = httpx.AsyncClient()

# Cache for latest Minecraft release version
# Stores a dictionary with 'value' and 'timestamp'
_latest_mc_version_cache = {"value": None, "timestamp": 0}
CACHE_DURATION_SECONDS = 3600  # 1 hour

async def get_latest_minecraft_release_version() -> str:
  """
  Helper function to get the ID of the latest Minecraft release version.
  Includes in-memory caching that refreshes every hour.
  """
  current_time = time.time()

  # Check if the cached value is still fresh
  if _latest_mc_version_cache["value"] and (current_time - _latest_mc_version_cache["timestamp"]) < CACHE_DURATION_SECONDS:
    return _latest_mc_version_cache["value"]

  # If cache is stale or empty, fetch new data
  try:
    response = await http_client.get("https://piston-meta.mojang.com/mc/game/version_manifest.json")
    response.raise_for_status()
    data = response.json()
    latest_release_id = next(
      (version["id"] for version in data.get("versions", []) if version.get("type") == "release"),
      None
    )
    if not latest_release_id:
      raise ValueError("Could not find the latest Minecraft release version.")
    
    # Update cache
    _latest_mc_version_cache["value"] = latest_release_id
    _latest_mc_version_cache["timestamp"] = current_time
    
    return latest_release_id
  except httpx.HTTPStatusError as e:
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to Mojang API to get latest Minecraft version: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get latest Minecraft version: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while fetching latest Minecraft version: {e}"
    )


@app.get(
  "/mc/versions",
  response_model=List[str],
  summary="Get Minecraft Versions",
  description="Retrieves the list of Minecraft versions. Can be filtered by 'release' or 'snapshot' type."
)
async def get_minecraft_versions(
  version_type: Optional[str] = Query(
    None,
    description="Optional filter for version type: 'release' or 'snapshot'. If not provided, all versions are returned."
  )
) -> List[str]:
  """
  Retrieves a list of Minecraft versions from Mojang's manifest, with optional filtering by type.
  """
  if version_type and version_type not in ["release", "snapshot"]:
    raise HTTPException(
      status_code=400,
      detail="Invalid version type. Must be 'release', 'snapshot', or left empty."
    )

  try:
    response = await http_client.get("https://piston-meta.mojang.com/mc/game/version_manifest.json")
    response.raise_for_status()
    data = response.json()

    filtered_versions = [
      version["id"]
      for version in data.get("versions", [])
      if not version_type or version.get("type") == version_type
    ]
    return filtered_versions
  except httpx.HTTPStatusError as e:
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to Mojang API: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get Minecraft versions: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while processing Minecraft versions: {e}"
    )


@app.get(
  "/mc/loaders/fabric",
  response_model=List[str],
  summary="Get Fabric Loader versions",
  description="Retrieves the list of available Fabric Loader versions for a specific Minecraft version or the latest release."
)
async def get_fabric_versions(
  minecraft_version: Optional[str] = Query(
    None,
    description="Optional Minecraft version (e.g., '1.18.2', '1.20.1'). If not provided, uses the latest Minecraft release version."
  )
) -> List[str]:
  """
  Retrieves a list of Fabric loader versions for a given Minecraft version or the latest release version.
  """
  target_mc_version = minecraft_version
  if not target_mc_version:
    target_mc_version = await get_latest_minecraft_release_version()

  try:
    response = await http_client.get(f"https://meta.fabricmc.net/v2/versions/loader/{target_mc_version}")
    response.raise_for_status()
    data = response.json()

    fabric_versions = [item["loader"]["version"] for item in data if "loader" in item and "version" in item["loader"]]
    return fabric_versions
  except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
      raise HTTPException(
        status_code=404,
        detail=f"No Fabric versions found for Minecraft {target_mc_version}. Please check the Minecraft version."
      )
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to Fabric API: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get Fabric versions: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while processing Fabric versions: {e}"
    )


@app.get(
  "/mc/loaders/quilt",
  response_model=List[str],
  summary="Get Stable Quilt Loader Versions",
  description="Retrieves the list of stable Quilt Loader versions (excluding betas and pre-releases)."
)
async def get_quilt_versions() -> List[str]:
  """
  Retrieves a list of stable Quilt loader versions by parsing their Maven metadata XML.
  """
  try:
    response = await http_client.get("https://maven.quiltmc.org/repository/release/org/quiltmc/quilt-loader/maven-metadata.xml")
    response.raise_for_status()
    xml_data = response.text

    root = ET.fromstring(xml_data)
    versions_element = root.find(".//versions")
    
    stable_versions = []
    if versions_element is not None:
      for version_elem in versions_element.findall("version"):
        version = version_elem.text
        if version and "-beta" not in version and "-pre" not in version:
          stable_versions.append(version)
    
    stable_versions.sort(key=lambda s: [int(u) if u.isdigit() else u for u in re.split('([0-9]+)', s)], reverse=True)
    
    return stable_versions
  except httpx.HTTPStatusError as e:
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to Quilt repository: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get Quilt versions: {e}"
    )
  except ET.ParseError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Error parsing Quilt XML: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while processing Quilt versions: {e}"
    )


@app.get(
  "/mc/loaders/forge",
  response_model=List[str],
  summary="Get Forge versions",
  description="Retrieves the list of available Forge versions that match a specific Minecraft version or the latest release. Can return only the build version."
)
async def get_forge_versions(
  minecraft_version: Optional[str] = Query(
    None,
    description="Optional Minecraft version (e.g., '1.18.2', '1.20.1'). If not provided, uses the latest Minecraft release version."
  ),
  version_only: bool = Query(
    False,
    description="If true, returns only the Forge build version (e.g., '56.0.8' instead of '1.21.6-56.0.8')."
  )
) -> List[str]:
  """
  Retrieves a list of Forge versions for a given Minecraft version or the latest release version.
  Can optionally return only the build version without the Minecraft version prefix.
  """
  target_mc_version = minecraft_version
  if not target_mc_version:
    target_mc_version = await get_latest_minecraft_release_version()

  try:
    response = await http_client.get("https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml")
    response.raise_for_status()
    xml_data = response.text

    root = ET.fromstring(xml_data)
    versions_element = root.find(".//versions")
    
    filtered_forge_versions = []
    if versions_element is not None:
      for version_elem in versions_element.findall("version"):
        version = version_elem.text
        if version and version.startswith(f"{target_mc_version}-"):
          if version_only:
            # Extract the part after the Minecraft version and the first hyphen
            # Example: "1.21.6-56.0.8" -> "56.0.8"
            extracted_version = version.split(f"{target_mc_version}-", 1)[-1]
            filtered_forge_versions.append(extracted_version)
          else:
            filtered_forge_versions.append(version)
    
    return filtered_forge_versions
  except httpx.HTTPStatusError as e:
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to Forge repository: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get Forge versions: {e}"
    )
  except ET.ParseError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Error parsing Forge XML: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while processing Forge versions: {e}"
    )


@app.get(
  "/mc/loaders/neoforge",
  response_model=List[str],
  summary="Get NeoForge Versions",
  description="Retrieves the list of NeoForge versions for a specific Minecraft version or the latest release. Can filter by 'release' type to exclude betas."
)
async def get_neoforge_versions(
  minecraft_version: Optional[str] = Query(
    None,
    description="Optional Minecraft version. If not provided, uses the latest Minecraft release version. Note: This parameter is primarily for consistency, the NeoForge API does not always filter by MC version directly in its metadata."
  ),
  version_type: Optional[str] = Query(
    None,
    description="Optional filter for NeoForge version type: 'release' to exclude beta versions. If not provided, all versions are returned."
  )
) -> List[str]:
  """
  Retrieves a list of NeoForge versions by parsing their Maven metadata XML.
  Can filter out beta versions if 'type' is 'release'.
  """
  # Note: The minecraft_version parameter is not directly used for filtering in the NeoForge
  # Maven metadata URL or the core logic, mirroring the original JS. It's kept for API consistency.
  # The actual filtering for NeoForge happens based on the 'type' query parameter if 'release' is specified.
  
  # We still need to get the latest MC version for consistency in the parameter
  # although it's not used for NeoForge API itself.
  target_mc_version = minecraft_version
  if not target_mc_version:
    target_mc_version = await get_latest_minecraft_release_version()

  if version_type and version_type not in ["release"]: # Only 'release' is supported for filtering out betas
    raise HTTPException(
      status_code=400,
      detail="Invalid NeoForge version type. Must be 'release' or left empty."
    )

  try:
    response = await http_client.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
    response.raise_for_status()
    xml_data = response.text

    root = ET.fromstring(xml_data)
    versions_element = root.find(".//versions")
    
    neoforge_versions = []
    if versions_element is not None:
      for version_elem in versions_element.findall("version"):
        version = version_elem.text
        if version:
          # Apply filtering based on 'version_type' for NeoForge
          if version_type == "release" and "-beta" in version:
            continue # Skip beta versions if 'release' type is requested
          neoforge_versions.append(version)
    
    # Reverse to get latest first as per original JS example's behavior
    neoforge_versions.reverse() 
    
    return neoforge_versions
  except httpx.HTTPStatusError as e:
    raise HTTPException(
      status_code=e.response.status_code,
      detail=f"Error connecting to NeoForge repository: {e.response.text}"
    )
  except httpx.RequestError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Network error while trying to get NeoForge versions: {e}"
    )
  except ET.ParseError as e:
    raise HTTPException(
      status_code=500,
      detail=f"Error parsing NeoForge XML: {e}"
    )
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Internal server error while processing NeoForge versions: {e}"
    )
