def get_api_endpoints(config: dict) -> dict:
    url = config["diagho_api"]["url"].rstrip("/")
    return {
        "healthcheck": f"{url}/healthcheck",
        "login": f"{url}/auth/login/",
        "get_user": f"{url}/users/me",
        "get_biofile": f"{url}/bio-files",
        "post_biofile_snv": f"{url}/bio-files/snv/",
        "post_biofile_cnv": f"{url}/bio-files/cnv/",
        "post_config": f"{url}/configurations/",
        "get_project": f"{url}/projects/",
    }
