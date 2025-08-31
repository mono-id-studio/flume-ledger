def test_service_instance_factory_with_service(
    service_factory, service_instance_factory
):
    # explicitly create a service
    s = service_factory(name="explicit-service")
    inst = service_instance_factory(service=s)

    assert inst.service == s
