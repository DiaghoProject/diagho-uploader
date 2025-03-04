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
        'post_config': f"{url_diagho_api}configurations/configurations/",
        'get_project': f"{url_diagho_api}projects/projects/"
    }
    # API 0.4.0
    # TODO: vérifier la présence de slash dans l'api_handler
    # TODO: remplacer loading_status par get_biofiles dans api_handler
    # url_diagho_api = config['diagho_api']['url'].removesuffix('/')
    # return {
    #     'healthcheck': f"{url_diagho_api}/healthcheck",
    #     'login': f"{url_diagho_api}/auth/login",
    #     'get_user': f"{url_diagho_api}/users/me",
    #     'get_biofile': f"{url_diagho_api}/bio-files",
    #     'post_biofile_snv': f"{url_diagho_api}/bio-files/snv",
    #     'post_biofile_cnv': f"{url_diagho_api}/bio-files/cnv",
    #     'post_config': f"{url_diagho_api}/configurations,
    #     'get_project': f"{url_diagho_api}/projects"
    # }