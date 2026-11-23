import sys

if len(sys.argv) > 2 and sys.argv[1:3] == ['limitset', 'baseline']:
    from pipeline.limitset_baselines import main
    main(sys.argv[3:])
elif len(sys.argv) > 1 and sys.argv[1] == 'limitset':
    from pipeline.limitset import main
    main(sys.argv[2:])
else:
    from pipeline.run import main
    main()
