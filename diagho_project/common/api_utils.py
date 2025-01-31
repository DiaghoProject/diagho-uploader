def get_api_endpoints(config):
    """Retourne les URLs de l'API à partir du fichier de configuration."""
    url_diagho_api = config['diagho_api']['url']
    return {
        'healthcheck': f"{url_diagho_api}healthcheck",
        'login': f"{url_diagho_api}auth/login/",
        'get_user': f"{url_diagho_api}accounts/users/me",
        'get_biofile': f"{url_diagho_api}bio_files/files",
        'post_biofile_snv': f"{url_diagho_api}bio_files/files/snv/",
        'post_biofile_cnv': f"{url_diagho_api}bio_files/files/cnv/",
        'loading_status': f"{url_diagho_api}bio_files/files/",
        'config': f"{url_diagho_api}configurations/configurations/"
    }
