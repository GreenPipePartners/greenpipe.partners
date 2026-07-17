SUPPORTED_PLATFORMS = [
    ("factorytalk", "Rockwell FactoryTalk View ME/SE", "XML graphics; CSV/XML tags and alarms", "High", "ME .MER files must be restorable"),
    ("factorytalk-optix", "Rockwell FactoryTalk Optix", "YAML model, C# code, Git resources", "High", "Custom NetLogic requires rewriting"),
    ("wincc-oa", "Siemens WinCC OA", "ASCII exports, .pnl panels, .ctl scripts, APIs", "High", "Proprietary UI semantics"),
    ("wincc-unified", "Siemens WinCC Unified/Professional", "TIA Openness API, XML and CSV", "High", "Coverage varies by TIA version"),
    ("twincat-hmi", "Beckhoff TwinCAT HMI", "JSON views and HTML/CSS/JS resources", "High", "Custom controls need manual conversion"),
    ("mapp-view", "B&R mapp View", "XML configuration and web assets", "High", "Widget/action mapping is proprietary"),
    ("zenon", "COPA-DATA zenon", "XML exports and Engineering Studio API", "High", "Some modules need separate extraction"),
    ("movicon", "Emerson Movicon / Movicon.NExT", "XML resources, exports, scripting APIs", "High-Medium", "Native formats vary by generation"),
    ("pcvue", "PcVue", "XML/CSV export and automation interfaces", "High-Medium", "Mimic extraction must be version-tested"),
    ("vtscada", "VTScada", "Text source, tag exports and APIs", "High-Medium", "Screens can contain substantial source logic"),
    ("fuxa", "FUXA", "JSON project exports and source", "High", "Smaller installed base"),
    ("rapid-scada", "Rapid SCADA", "XML/database configuration and source", "High", "Visualization mapping needs an adapter"),
    ("scada-lts", "Scada-LTS / ScadaBR", "SQL/JSON configuration and source", "High-Medium", "Older visualization models"),
    ("plant-scada", "AVEVA Plant SCADA / Citect", "DBF/CSV, Cicode, Graphics Builder API", "Medium-High", "Vendor tooling required"),
    ("intouch", "AVEVA InTouch", "DB Dump/Load CSV, scripts, WindowMaker", "Medium", "Vendor tooling required"),
    ("system-platform", "AVEVA System Platform / OMI", "GRAccess, Galaxy exports, packages", "Medium", "Vendor tooling required"),
    ("aveva-edge", "AVEVA Edge / InduSoft", "Tag worksheets, CSV, scripts, projects", "Medium", "Vendor tooling required"),
    ("ifix", "GE Proficy iFIX", "Database CSV and VBA/COM picture model", "Medium", "Vendor tooling required"),
    ("cimplicity", "GE Proficy CIMPLICITY", "Point/alarm exports and CimEdit API", "Medium", "Vendor tooling required"),
    ("genesis64", "ICONICS GENESIS64", "GraphWorX resources, exports and APIs", "Medium", "Vendor tooling required"),
    ("geo-scada", "Schneider Geo SCADA Expert", "Automation Interface, SQL and APIs", "Medium", "Vendor tooling required"),
    ("wincc-classic", "Siemens WinCC V7/Classic", "Exports, Graphics APIs, C/VBS scripts", "Medium", "Vendor tooling required"),
    ("red-lion", "Red Lion Crimson", "Project database and tag exports", "Custom review", "Version and source backup quality vary"),
    ("other", "Other HMI/SCADA platform", "Provide an extractable source backup", "Custom review", "Feasibility confirmed during quote review"),
]

IGNITION_SOURCE_CONVERSION_CENTS = 80000
OTHER_SOURCE_CONVERSION_CENTS = 300000

PLATFORM_VENDORS = {
    "aveva-edge": "AVEVA",
    "cimplicity": "GE Vernova",
    "factorytalk": "Rockwell Automation",
    "factorytalk-optix": "Rockwell Automation",
    "fuxa": "FUXA",
    "genesis64": "ICONICS",
    "geo-scada": "Schneider Electric",
    "ifix": "GE Vernova",
    "ignition": "Inductive Automation",
    "intouch": "AVEVA",
    "mapp-view": "B&R",
    "movicon": "Emerson",
    "other": "Other",
    "pcvue": "PcVue Solutions",
    "plant-scada": "AVEVA",
    "rapid-scada": "Rapid SCADA",
    "red-lion": "Red Lion",
    "scada-lts": "Scada-LTS",
    "system-platform": "AVEVA",
    "twincat-hmi": "Beckhoff",
    "vtscada": "Trihedral",
    "wincc-classic": "Siemens",
    "wincc-oa": "Siemens",
    "wincc-unified": "Siemens",
    "zenon": "COPA-DATA",
}


def source_platform_groups():
    grouped = {}
    choices = [("ignition", "Ignition")] + [
        (code, name) for code, name, *_ in SUPPORTED_PLATFORMS
    ]
    for code, name in choices:
        grouped.setdefault(PLATFORM_VENDORS[code], []).append((code, name))
    return [
        (vendor, sorted(platforms, key=lambda platform: platform[1].casefold()))
        for vendor, platforms in sorted(
            grouped.items(),
            key=lambda item: (item[0] == "Other", item[0].casefold()),
        )
    ]


SOURCE_PLATFORM_GROUPS = source_platform_groups()
