data "aviatrix_smart_groups" "foo" {
    depends_on = [ aviatrix_web_group.web_groups ]
}